import copy
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import types

import study_sync as s

NOW = s.timestamp("2026-10-22T20:00:00Z")


def sample():
    return {"schema_version": 1, "source": "blueprint_mcat", "learner_id": "DEMO_ONLY",
            "captured_at": "2026-10-22T19:00:00Z",
            "coverage": {"attempts": "partial", "assessments": "unavailable", "activities": "unavailable"},
            "attempts": [{"id": "attempt-1", "question_id": "question-1", "section": "BB",
                          "topic": "Enzyme kinetics", "skill": "Data interpretation", "correct": False,
                          "occurred_at": "2026-10-22T18:00:00Z", "updated_at": "2026-10-22T18:00:00Z",
                          "seconds": 110}], "assessments": [], "activities": []}


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = s.connect(Path(self.temp.name) / "study.sqlite")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_reimport_does_not_duplicate_or_refresh_source_capture(self):
        d = sample()
        s.ingest(self.db, d, NOW)
        result = s.ingest(self.db, d, NOW + timedelta(days=10))
        out = s.export_state(self.db, NOW + timedelta(days=10))
        self.assertEqual(result["status"], "already_imported")
        self.assertEqual(len(out["records"]["attempts"]), 1)
        self.assertEqual(out["source_age_hours"], 241)

    def test_partial_capture_does_not_remove_history(self):
        d = sample()
        s.ingest(self.db, d, NOW)
        d["attempts"] = []
        d["captured_at"] = "2026-10-22T19:30:00Z"
        s.ingest(self.db, d, NOW)
        self.assertEqual(len(s.export_state(self.db, NOW)["records"]["attempts"]), 1)

    def test_retake_is_separate_and_unique_question_count_is_one(self):
        d = sample()
        row = dict(d["attempts"][0], id="attempt-2", correct=True)
        d["attempts"].append(row)
        s.ingest(self.db, d, NOW)
        stats = s.export_state(self.db, NOW)["topic_summaries"][0]["windows"]["24h"]
        self.assertEqual((stats["attempts"], stats["unique_questions"], stats["accuracy"]), (2, 1, 0.5))

    def test_new_revision_wins_and_old_revision_is_retained(self):
        old = sample()
        new = copy.deepcopy(old)
        new["attempts"][0].update(correct=True, updated_at="2026-10-22T18:30:00Z")
        s.ingest(self.db, new, NOW)
        s.ingest(self.db, old, NOW)
        self.assertTrue(s.export_state(self.db, NOW)["records"]["attempts"][0]["correct"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM revisions").fetchone()[0], 2)

    def test_same_revision_conflict_rolls_back_entire_batch(self):
        d = sample()
        s.ingest(self.db, d, NOW)
        d["attempts"].insert(0, dict(d["attempts"][0], id="attempt-new"))
        d["attempts"][1]["correct"] = True
        with self.assertRaises(ValueError):
            s.ingest(self.db, d, NOW)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM records").fetchone()[0], 1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM syncs").fetchone()[0], 1)

    def test_account_mixing_is_rejected(self):
        d = sample()
        s.ingest(self.db, d, NOW)
        d["learner_id"] = "OTHER"
        with self.assertRaises(ValueError):
            s.ingest(self.db, d, NOW)

    def test_boolean_strings_and_naive_dates_and_nan_are_rejected(self):
        for key, value in (("correct", "false"), ("occurred_at", "2026-10-22T18:00:00"),
                           ("seconds", float("nan"))):
            d = sample()
            d["attempts"][0][key] = value
            with self.assertRaises(ValueError):
                s.ingest(self.db, d, NOW)

    def test_windows_and_unanswered_denominator(self):
        d = sample()
        d["attempts"].extend([
            dict(d["attempts"][0], id="unanswered", correct=None),
            dict(d["attempts"][0], id="old", occurred_at="2026-10-20T18:00:00Z", correct=True),
        ])
        s.ingest(self.db, d, NOW)
        w = s.export_state(self.db, NOW)["topic_summaries"][0]["windows"]
        self.assertEqual(w["24h"]["accuracy"], 0)
        self.assertEqual(w["24h"]["unanswered"], 1)
        self.assertEqual(w["7d"]["accuracy"], 0.5)

    def test_learning_observation_survives_source_sync(self):
        observation = {"id": "obs-1", "occurred_at": "2026-10-22T18:00:00Z", "topic": "general",
                       "kind": "personal_context", "text": "Learner reports a busy week.",
                       "source": "learner_report", "evidence_ids": []}
        s.record_observation(self.db, observation)
        s.record_observation(self.db, observation)
        s.ingest(self.db, sample(), NOW)
        self.assertEqual(s.export_state(self.db, NOW)["local_observations"], [observation])
        observation["text"] = "Changed text"
        with self.assertRaises(ValueError):
            s.record_observation(self.db, observation)

    def test_unavailable_new_collection_does_not_mask_old_capture(self):
        d = sample()
        s.ingest(self.db, d, NOW)
        d.update(attempts=[], captured_at="2026-10-22T19:30:00Z")
        d["coverage"]["attempts"] = "unavailable"
        s.ingest(self.db, d, NOW)
        freshness = s.export_state(self.db, NOW)["freshness_by_collection"]["attempts"]
        self.assertEqual(freshness["last_available_capture"], "2026-10-22T19:00:00.000000Z")
        self.assertIsNone(freshness["last_complete_capture"])

    def test_subsecond_captures_sort_chronologically(self):
        d = sample()
        s.ingest(self.db, d, NOW)
        d["captured_at"] = "2026-10-22T19:00:00.100Z"
        s.ingest(self.db, d, NOW)
        self.assertEqual(s.export_state(self.db, NOW)["source_captured_at"], "2026-10-22T19:00:00.100000Z")


class DriveTests(unittest.TestCase):
    def test_create_then_update_stable_file(self):
        # Transport-level fake; live Google OAuth and Drive still need account validation.
        import publish_drive
        fake = types.ModuleType("googleapiclient.http")
        fake.MediaIoBaseUpload = MagicMock()
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {"googleapiclient.http": fake}):
            path, mapping = Path(tmp) / "state.json", Path(tmp) / "mapping.json"
            s.atomic_json(path, {"schema_version": 1, "product": "MCAT", "learner_id": "DEMO"})
            service = MagicMock()
            files = service.files.return_value
            files.list.return_value.execute.return_value = {"files": []}
            files.create.return_value.execute.return_value = {"id": "file-123"}
            publish_drive.publish(service, path, mapping)
            props = files.create.call_args.kwargs["body"]["appProperties"]
            files.get.return_value.execute.return_value = {"appProperties": props}
            files.update.return_value.execute.return_value = {"id": "file-123"}
            publish_drive.publish(service, path, mapping)
            self.assertEqual(files.create.call_count, 1)
            self.assertEqual(files.update.call_args.kwargs["fileId"], "file-123")


if __name__ == "__main__":
    unittest.main()

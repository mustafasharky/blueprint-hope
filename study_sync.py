"""Offline MCAT evidence store. No Blueprint endpoints or credentials are assumed."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sqlite3
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
SECTIONS = {"CP", "CARS", "BB", "PS"}


def utcnow():
    return datetime.now(UTC)


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamps must be ISO 8601 strings with a timezone")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return result.astimezone(UTC)


def iso(value):
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".writing-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS records (
      kind TEXT NOT NULL, id TEXT NOT NULL, updated_at TEXT NOT NULL,
      payload TEXT NOT NULL, PRIMARY KEY(kind,id));
    CREATE TABLE IF NOT EXISTS revisions (
      kind TEXT NOT NULL, id TEXT NOT NULL, hash TEXT NOT NULL,
      payload TEXT NOT NULL, observed_at TEXT NOT NULL,
      PRIMARY KEY(kind,id,hash));
    CREATE TABLE IF NOT EXISTS syncs (
      hash TEXT PRIMARY KEY, captured_at TEXT NOT NULL,
      imported_at TEXT NOT NULL, coverage TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS observations (
      id TEXT PRIMARY KEY, payload TEXT NOT NULL);
    """)
    return db


def nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")


def validate_snapshot(data, now=None):
    now = now or utcnow()
    expected = {"schema_version", "source", "learner_id", "captured_at",
                "coverage", "attempts", "assessments", "activities"}
    if not isinstance(data, dict) or set(data) != expected:
        raise ValueError(f"snapshot must have exactly these fields: {sorted(expected)}")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("unsupported schema_version")
    if data["source"] != "blueprint_mcat":
        raise ValueError("source must be blueprint_mcat")
    nonempty(data["learner_id"], "learner_id")
    captured = timestamp(data["captured_at"])
    if captured > now + timedelta(minutes=5):
        raise ValueError("capture is in the future")
    coverage = data["coverage"]
    if not isinstance(coverage, dict) or set(coverage) != {"attempts", "assessments", "activities"}:
        raise ValueError("coverage must describe all three collections")
    if any(v not in {"complete", "partial", "unavailable"} for v in coverage.values()):
        raise ValueError("coverage must use complete/partial/unavailable")
    for kind in ("attempts", "assessments", "activities"):
        if not isinstance(data[kind], list):
            raise ValueError(f"{kind} must be a list")
        if coverage[kind] == "unavailable" and data[kind]:
            raise ValueError("unavailable collections must be empty")
        seen = set()
        for row in data[kind]:
            if not isinstance(row, dict):
                raise ValueError("each record must be an object")
            common = {"id", "updated_at", "occurred_at"}
            if kind == "attempts":
                required = common | {"question_id", "section", "topic", "skill", "correct"}
                optional = {"assessment_id", "seconds", "answer_change", "bookmarked", "mode"}
            elif kind == "assessments":
                required = common | {"name", "scores"}
                optional = {"mode"}
            else:
                required = common | {"name", "type", "status"}
                optional = {"topic"}
            if not required <= row.keys() or row.keys() - required - optional:
                raise ValueError(f"{kind}: missing or unknown fields; consult FORMAT.md")
            nonempty(row["id"], "record id")
            if row["id"] in seen:
                raise ValueError("duplicate record id within a snapshot")
            seen.add(row["id"])
            updated, occurred = timestamp(row["updated_at"]), timestamp(row["occurred_at"])
            if occurred > updated or updated > captured:
                raise ValueError("require occurred_at <= updated_at <= captured_at")
            if kind == "attempts":
                nonempty(row["question_id"], "question_id")
                nonempty(row["topic"], "topic")
                if row["skill"] is not None:
                    nonempty(row["skill"], "skill")
                if row["section"] not in SECTIONS:
                    raise ValueError("invalid section")
                if row["correct"] is not None and type(row["correct"]) is not bool:
                    raise ValueError("correct must be true, false, or null (unanswered)")
                seconds = row.get("seconds")
                if seconds is not None and (type(seconds) not in (int, float) or
                                           not math.isfinite(seconds) or seconds < 0):
                    raise ValueError("seconds must be a finite nonnegative number or null")
                if row.get("answer_change") not in {None, "none", "right_to_wrong", "wrong_to_right", "wrong_to_wrong"}:
                    raise ValueError("invalid answer_change")
                if row.get("bookmarked") is not None and type(row["bookmarked"]) is not bool:
                    raise ValueError("bookmarked must be boolean or null")
                if row.get("assessment_id") is not None:
                    nonempty(row["assessment_id"], "assessment_id")
            elif kind == "assessments":
                nonempty(row["name"], "name")
                if not isinstance(row["scores"], dict) or set(row["scores"]) - SECTIONS - {"total"}:
                    raise ValueError("scores must map MCAT sections/total to numbers or null")
                for value in row["scores"].values():
                    if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                        raise ValueError("invalid score")
            else:
                for key in ("name", "type", "status"):
                    nonempty(row[key], key)
            for key in ("mode", "topic"):
                if key in row and row[key] is not None:
                    nonempty(row[key], key)
    return data


def ingest(db, data, now=None):
    now = now or utcnow()
    validate_snapshot(data, now)
    snapshot_hash = digest(data)
    counts = {"inserted": 0, "updated": 0, "unchanged": 0, "older_ignored": 0}
    with db:
        # Serialize readers of old revisions before any merge decisions.
        db.execute("BEGIN IMMEDIATE")
        owner = db.execute("SELECT value FROM meta WHERE key='learner_id'").fetchone()
        if owner and owner[0] != data["learner_id"]:
            raise ValueError("use a separate database for each learner")
        db.execute("INSERT OR IGNORE INTO meta VALUES ('learner_id',?)", (data["learner_id"],))
        if db.execute("SELECT 1 FROM syncs WHERE hash=?", (snapshot_hash,)).fetchone():
            return {"status": "already_imported", **counts}
        for kind in ("attempts", "assessments", "activities"):
            for raw in data[kind]:
                row = dict(raw)
                row["updated_at"] = iso(timestamp(row["updated_at"]))
                row["occurred_at"] = iso(timestamp(row["occurred_at"]))
                payload = encode(row)
                old = db.execute("SELECT updated_at,payload FROM records WHERE kind=? AND id=?",
                                 (kind, row["id"])).fetchone()
                db.execute("INSERT OR IGNORE INTO revisions VALUES (?,?,?,?,?)",
                           (kind, row["id"], digest(row), payload, iso(now)))
                if old and timestamp(old[0]) > timestamp(row["updated_at"]):
                    counts["older_ignored"] += 1
                    continue
                if old and old[0] == row["updated_at"]:
                    if old[1] != payload:
                        raise ValueError("conflicting payloads at the same record revision")
                    counts["unchanged"] += 1
                    continue
                db.execute("INSERT INTO records VALUES (?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET "
                           "updated_at=excluded.updated_at,payload=excluded.payload",
                           (kind, row["id"], row["updated_at"], payload))
                counts["updated" if old else "inserted"] += 1
        db.execute("INSERT INTO syncs VALUES (?,?,?,?)",
                   (snapshot_hash, iso(timestamp(data["captured_at"])), iso(now), encode(data["coverage"])))
    return {"status": "imported", **counts}


def record_observation(db, data):
    required = {"id", "occurred_at", "topic", "kind", "text", "source", "evidence_ids"}
    if not isinstance(data, dict) or set(data) != required:
        raise ValueError("observation fields must be: " + ", ".join(sorted(required)))
    for key in ("id", "topic", "text"):
        nonempty(data[key], key)
    timestamp(data["occurred_at"])
    if data["kind"] not in {"personal_context", "misconception", "practice_result", "review_due"}:
        raise ValueError("unknown observation kind")
    if data["source"] not in {"learner_report", "tutor_observation"}:
        raise ValueError("unknown observation source")
    if not isinstance(data["evidence_ids"], list):
        raise ValueError("evidence_ids must be a list")
    for item in data["evidence_ids"]:
        nonempty(item, "evidence id")
    with db:
        old = db.execute("SELECT payload FROM observations WHERE id=?", (data["id"],)).fetchone()
        if old and old[0] != encode(data):
            raise ValueError("observation ids are immutable; append a correction with a new id")
        db.execute("INSERT OR IGNORE INTO observations VALUES (?,?)", (data["id"], encode(data)))


def metrics(rows):
    answered = [r for r in rows if r["correct"] is not None]
    correct = sum(r["correct"] for r in answered)
    times = [r["seconds"] for r in rows if r.get("seconds") is not None]
    return {"attempts": len(rows), "answered": len(answered), "correct": correct,
            "unanswered": len(rows) - len(answered),
            "accuracy": correct / len(answered) if answered else None,
            "unique_questions": len({r["question_id"] for r in rows}),
            "mean_seconds": sum(times) / len(times) if times else None,
            "timed_observations": len(times)}


def export_state(db, as_of=None):
    now = as_of or utcnow()
    owner = db.execute("SELECT value FROM meta WHERE key='learner_id'").fetchone()
    if not owner:
        raise ValueError("import a normalized snapshot first")
    records = {k: [] for k in ("attempts", "assessments", "activities")}
    for kind, payload in db.execute("SELECT kind,payload FROM records ORDER BY kind,id"):
        records[kind].append(json.loads(payload))
    latest = db.execute("SELECT captured_at,coverage FROM syncs ORDER BY captured_at DESC,imported_at DESC LIMIT 1").fetchone()
    if timestamp(latest[0]) > now:
        raise ValueError("as_of must not precede the newest capture")
    grouped = defaultdict(list)
    for row in records["attempts"]:
        grouped[(row["section"], row["topic"], row["skill"])].append(row)
    summaries = []
    for (section, topic, skill), rows in grouped.items():
        windows = {}
        for label, days in (("24h", 1), ("7d", 7), ("30d", 30), ("all", None)):
            subset = [r for r in rows if timestamp(r["occurred_at"]) <= now and
                      (days is None or timestamp(r["occurred_at"]) > now - timedelta(days=days))]
            windows[label] = metrics(subset)
        recent = windows["30d"]
        n, correct = recent["answered"], recent["correct"]
        summaries.append({"section": section, "topic": topic, "skill": skill,
                          "windows": windows,
                          "smoothed_30d_error_rate": (n - correct + 1) / (n + 2) if n else None,
                          "evidence_ids": [r["id"] for r in rows],
                          "last_practiced_at": max(r["occurred_at"] for r in rows)})
    summaries.sort(key=lambda r: (r["section"], r["topic"], r["skill"] or ""))
    sync_history = [{"snapshot_hash": h, "captured_at": c, "imported_at": i,
                     "coverage": json.loads(v)} for h, c, i, v in db.execute(
                         "SELECT hash,captured_at,imported_at,coverage FROM syncs ORDER BY captured_at")]
    freshness = {}
    for kind in records:
        available = [s["captured_at"] for s in sync_history if s["coverage"][kind] != "unavailable"]
        complete = [s["captured_at"] for s in sync_history if s["coverage"][kind] == "complete"]
        freshness[kind] = {"last_available_capture": max(available, default=None),
                           "last_complete_capture": max(complete, default=None)}
    return {"schema_version": 1, "product": "MCAT", "learner_id": owner[0],
            "generated_at": iso(now), "source_captured_at": latest[0],
            "source_age_hours": (now - timestamp(latest[0])).total_seconds() / 3600,
            "latest_capture_coverage": json.loads(latest[1]),
            "freshness_by_collection": freshness,
            "sync_history": sync_history, "records": records, "topic_summaries": summaries,
            "local_observations": [json.loads(r[0]) for r in db.execute(
                "SELECT payload FROM observations ORDER BY id")],
            "interpretation": [
                "Missing source records are retained; absence is not a deletion.",
                "Accuracy excludes unanswered items. Retakes remain separate attempts.",
                "Repeated-question accuracy does not demonstrate transfer to new questions.",
                "Smoothed error uses Beta(1,1); it is a descriptive heuristic, not a mastery probability.",
                "Question timing may exclude passage reading; do not impose a universal time target.",
                "Personal context is reported evidence, not a diagnosis.",
                "Cloud tutor memory is maintained separately and must also be read."]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, default=Path("private/study.sqlite"))
    sub = p.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import", help="Import the normalized contract, NOT a raw Blueprint export")
    imp.add_argument("input", type=Path)
    obs = sub.add_parser("observe", help="Append a structured local learning observation")
    obs.add_argument("input", type=Path)
    exp = sub.add_parser("export")
    exp.add_argument("--out", type=Path, default=Path("private/study_state.json"))
    exp.add_argument("--as-of", help="ISO timestamp for reproducible demos")
    args = p.parse_args()
    db = connect(args.db)
    try:
        if args.command == "import":
            print(encode(ingest(db, json.loads(args.input.read_text(encoding="utf-8")))))
        elif args.command == "observe":
            record_observation(db, json.loads(args.input.read_text(encoding="utf-8")))
            print("Observation stored")
        else:
            state = export_state(db, timestamp(args.as_of) if args.as_of else None)
            atomic_json(args.out, state)
            print(str(args.out.resolve()))
    finally:
        db.close()


if __name__ == "__main__":
    main()

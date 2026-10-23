# Normalized MCAT data contract, version 1

This is OUR adapter contract. It is not a claimed Blueprint export schema.
Read `examples/normalized_snapshot.json` for a complete synthetic instance.

## Input snapshot

Every snapshot has exactly these fields:

| Field | Meaning |
|---|---|
| `schema_version` | Integer `1` |
| `source` | `blueprint_mcat` |
| `learner_id` | Stable opaque learner identifier. Avoid email/name. One database per learner. |
| `captured_at` | When the extractor fetched the source, timezone-aware ISO 8601. Never replace it with import time. |
| `coverage` | Status of attempts, assessments, activities: `complete`, `partial`, or `unavailable`. |
| `attempts` | Question-level results, including repeated attempts as separate records. |
| `assessments` | Exam/section score records. |
| `activities` | Module or other progress records. Completion is not mastery. |

`complete` means the adapter traversed every page within its documented account scope.
Until that is verified use `partial`. `unavailable` requires an empty collection.
Even complete snapshots do not delete historical records; intentional source deletion
handling must be implemented explicitly later. Empty and unavailable are different.

Every record needs a stable `id`, `occurred_at`, and `updated_at`.
Require occurred_at <= updated_at <= captured_at. Times must include a timezone.
Use source revision timestamps when provided. If absent, the adapter must keep an
ID/content-hash map and assign a new observation revision only when content changes.
Do not generate new attempt IDs on every run. Do not key attempts by question ID alone.
Use the platform attempt/session identifier plus question ID when no individual result ID exists.

## Attempts

Required: `question_id`, `section`, `topic`, `skill`, `correct`, plus common fields.

- `section`: CP, CARS, BB, PS.
- `topic`: source label; do not invent fine-grained classifications from an aggregate score.
- `skill`: source reasoning skill label, or null if absent.
- `correct`: boolean; null means unanswered. Null is excluded from accuracy's denominator.
- Optional: `assessment_id`, `seconds`, `answer_change`, `bookmarked`, `mode`.
- `answer_change`: none, right_to_wrong, wrong_to_right, wrong_to_wrong, or null.
- `mode`: a source label such as timed/untimed, or null.
- No question/passage text, explanations, cookies, tokens, or login responses are accepted.

The adapter must distinguish first-time questions from repeated exposure where possible.
The core retains attempt IDs and question IDs and reports unique-question counts;
it does not claim to identify the first-ever exposure from an incomplete history.

## Assessments and activities

Assessments: `name`, `scores` (map of CP/CARS/BB/PS/total to numeric scores or null),
optional `mode`, plus common fields. Preserve source scores; never convert a Qbank
percent-correct to an estimated official MCAT score.

Activities: `name`, `type`, `status`, optional `topic`, plus common fields.
Examples: module completion, source-provided flashcard activity totals after extending
the schema if needed. Raw aggregate topic statistics, full study plans, target scores,
and flashcard ratings require a future explicit schema extension; do not pretend that
these fields are already exported by the starter. Store goals and constraints in memory.

## Learning observations

An observation is separately authored, not overwritten by Blueprint imports:
`id`, `occurred_at`, `topic`, `kind`, `text`, `source`, `evidence_ids`.

Kinds: personal_context, misconception, practice_result, review_due.
Sources: learner_report or tutor_observation. Use stable evidence IDs for observed
mistakes; user-reported context may have an empty list. IDs are immutable and retry-safe.
Corrections are new observations referring to the superseded observation.

## Output and ownership

`study_state.json` contains current normalized records, source freshness and coverage,
sync history, local observations, and topic/skill summaries for rolling 24h/7d/30d/all.
Windows use `(as_of - duration, as_of]`. These are rolling windows, not calendar dates.

SQLite preserves prior revisions and is the local source of truth. The JSON export
is a replaceable view. The publisher alone owns the Drive snapshot. ChatGPT owns a
SEPARATE tutor-memory document. Every brief must read both current sources.
Do not merge JSON blindly with old chat text, and do not let two processes write
the same snapshot file. Configure local scheduling to disallow overlapping runs.

The starter keeps all history in one export for inspection. Before months of large
Qbank history exceed practical retrieval limits, partition historical attempts by
month and keep one small manifest containing exact IDs, hashes, coverage, summaries,
and recent attempts. A custom MCP query layer is preferable at that stage.

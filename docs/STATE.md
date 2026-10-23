# Current state

Last updated: 2026-10-23. Read this before continuing development.

## User goal and scope

One local Windows-friendly script: normal Blueprint MCAT browser login, reusable
session, all relevant learner performance exported into context, and eventually
automatic delivery to a persistent ChatGPT study project. The study assistant should
provide 5–10 minute daily practice targeting recent and persistent weaknesses, plus
weekly/monthly reviews and learner-supplied personal context.

The user explicitly clarified this is not a platform or hosted application. The
original OAuth requirement became a preference for normal browser sign-in with
saved cookies/storage. No live account has yet been explored.

## Implemented

| Component | Actual behavior | Validation |
|---|---|---|
| `blueprint_browser.py` | Dedicated Chrome profile; interactive capture; saved-URL replay; visible page text; value-free JSON field shapes | Helper tests and mocked browser objects; no live Blueprint run |
| `study_sync.py` | Strict normalized import; SQLite revisions; retakes; account isolation; local observations; JSON export; time-window summaries | Offline tests with synthetic data |
| `publish_drive.py` | Google desktop OAuth/PKCE; keyring storage; update one stable Drive file | Mocked create/update only; no live Google flow |
| `prompts/` | Evidence-based daily, weekly, monthly coaching instructions | Written templates; not configured in ChatGPT |
| Repository documents | Decisions, architecture, discovery checklist, roadmap, session handoff | Initial foundation |

Validation: `python3 -m unittest discover -v` passed all 20 tests in this repository
on 2026-10-23. Windows and live Blueprint behavior remain unverified.

## Not implemented or unverified

- Authenticated Blueprint account exploration; actual portal hosts and API routes.
- Extracting actual JSON performance-response values (only their shapes are observed).
- All exam/attempt enumeration, pagination, filter persistence, chart and iframe data.
- Mapping actual Blueprint responses into the normalized contract.
- Automatic ChatGPT file replacement or another fully automatic handoff.
- Persistent cloud tutoring-memory writeback and scheduled lessons.
- Windows/live browser verification and credential-expiry recovery against Blueprint.

Do not assume the cloud browser's account/session is the user's local browser session.
Do not claim the optional Drive path or a generic JSON upload updates a consumer
ChatGPT Project directly.

## Important limitations to preserve in messaging

`capture` collects selected visible views and labels coverage partial. Different UI
filters/tabs sharing a URL overwrite each other within a run. `sync` reopens saved
URLs, not the interactions needed to restore those filters. It uses a generic wait,
does not traverse pagination, and only detects some sign-in failure patterns. Session
cookies/storage may require another normal sign-in. These are discovery-stage limits.

The output `blueprint_capture.json` is not accepted by the normalized importer.
`publish_drive.py` expects `study_sync.py export` output, not raw browser captures.
The core's smoothed error statistic is descriptive, not a validated mastery score.

## Exact next development task

Conduct one authorized local Blueprint MCAT discovery session using
`docs/BLUEPRINT_DISCOVERY.md`:

1. Run capture on the user's computer and log in normally.
2. Open Analytics and one completed full-length score report.
3. Inspect the real performance JSON locally; record sanitized endpoint/schema facts.
4. Map stable learner, exam, session, question, and attempt IDs; identify pagination.
5. Create synthetic fixtures preserving the observed structure.
6. Implement one small vertical slice: one completed exam -> normalized attempts ->
   SQLite -> context export, with counts checked against the UI.

Do not expand the generic architecture before this vertical slice is proven.

## Repository setup status

The user supplied `https://github.com/mustafasharky/blueprint-hope.git` as the
canonical repository. GitHub MCP has write access; website sign-in is no longer
needed. The repository is public as observed on 2026-10-23. Its tracked files must
contain only source, project documents, prompts, and synthetic examples.

The initial 26-file source snapshot is published on `main` at
`4e8100f51de1b8e6b3e9e961a97b9ac0a7e1b34e`; the remote handoff file was read back
successfully. All 20 offline tests passed again before publication. This follow-up
records completion of the repository foundation. Read AGENTS.md and this file at
the beginning of future sessions, then check Git history and ROADMAP.md.

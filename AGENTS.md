# Project instructions

## Start every session

1. Read `docs/STATE.md` for actual implementation status and the next task.
2. Read `docs/DECISIONS.md` for the user's settled constraints.
3. Read the relevant code and `docs/ROADMAP.md`; do not rely on chat history.
4. Check `git status` before editing. Preserve unrelated user changes.

## Scope

Build a local Windows-friendly Python script that reuses a normal Blueprint MCAT
browser login, extracts learner performance, and updates context for an adaptive
ChatGPT study coach. The goal is a repeatable local command, not a hosted platform.
Google Drive is optional. Do not make it a prerequisite for browser extraction.

## Current truth

The browser helper captures visible report text and JSON field shapes only.
It does not collect complete performance-response values, enumerate all attempts,
or automatically upload to ChatGPT. The normalized SQLite engine is implemented
but is not wired to actual Blueprint responses. Never describe these gaps as done.
No live Blueprint session, live Drive upload, or scheduled coaching run has been
verified. Consult STATE.md for changes to this baseline.

## Work rules

- Use actual observed Blueprint fields, URLs, selectors, and pagination. Do not
  invent endpoints, OAuth clients, or private schemas.
- Login is normal user-directed sign-in in a dedicated local browser profile.
  Handle session expiry visibly. Do not bypass MFA, access controls, or bot checks.
- Keep browser profiles, cookies, tokens, real learner exports, databases, and
  screenshots under ignored `private/`. Never commit them, even to a private repo.
- Commit only synthetic or carefully sanitized fixtures. Review both values and
  URLs/keys for identifying data. Do not commit an entire paid question bank.
- Preserve attempt identity, retakes, revisions, source timestamps, and capture
  coverage. Partial retrieval must not look like an empty complete account.
- Keep source performance and tutoring observations separately owned so exports
  cannot erase learning memory. Update observed mastery only after real evidence.
- Test helpers offline. Live account exploration requires the actual user's session;
  unit tests are not proof of live extraction or complete coverage.
- Keep this a small script project until evidence justifies additional structure.
  Do not add a server, hosting, accounts, or subscription dependencies by default.

## Verify and hand off

Run `python -m unittest discover -v` (Windows: `py -m unittest discover -v`).
Add focused tests when extraction/state behavior changes. Do not add tests for prose.
Before a handoff, update `docs/STATE.md` with what changed, the test result, unverified
assumptions, and the exact next action. Append a short entry to `docs/SESSION_LOG.md`.
Update DECISIONS.md only for actual decisions, not guesses. Keep this file concise.

When committing, inspect the staged file list and diff. The repository should
contain code, project documents, prompts, and synthetic examples only.

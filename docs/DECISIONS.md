# Decisions

These reflect the user's explicit choices and established implementation constraints.
Change them when the user changes direction or new observed evidence requires it.

| Decision | Reason / implication |
|---|---|
| Blueprint product: MCAT | Confirmed by the user; preserve MCAT section/topic/skill context. |
| Local executable script, Windows-friendly | User explicitly rejected a platform-style design. No server or hosting requirement. |
| Automatic updates are the eventual goal | A manual attachment is a temporary handoff, not completion. |
| Normal browser login with a dedicated persistent profile | Avoids needing a public Blueprint OAuth client; allows ordinary MFA and reauthentication. |
| Inspect the actual website before completing the exporter | UI-derived schemas and pagination must be observed, not guessed. |
| Preserve structured source history locally | SQLite holds current records and prior revisions; JSON is an export view. |
| Separate source performance from tutor memory | New exports must not erase misconceptions, explanations, or personal constraints. |
| Keep uncertain conclusions explicit | One missed question or a completed module is not proof of weakness or mastery. |
| Daily sessions should take 5–10 minutes | Include targeted retrieval/application and spaced review; weekly/monthly history informs selection. |
| Persist development context in the repository | AGENTS.md + STATE.md + decisions + discovery evidence reduce dependence on chat context. |
| Canonical repository: `mustafasharky/blueprint-hope` | Supplied by the user; observed public. Commit only code, documents, prompts, and synthetic examples; credentials and real learner data remain local. |

## Open decisions

- Exact fully automatic ChatGPT destination and upload/update mechanism.
- Whether to use optional Drive delivery or a local browser uploader.
- Exact authoritative store for tutor-memory writeback.
- Learner exam date, target score, availability, preferences, and daily schedule.
- Which additional progress/flashcard metadata the actual account exposes.

Do not infer these from unrelated user conversations. No learner-specific MCAT
performance or personal study constraints have been assessed in this project.

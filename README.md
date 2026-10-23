# Blueprint Hope

A local Python script that reuses a Blueprint MCAT browser session, exports study
evidence, and prepares context for a persistent adaptive study coach in ChatGPT.

Repository: [mustafasharky/blueprint-hope](https://github.com/mustafasharky/blueprint-hope).

**Status: working offline components and a partial browser capture helper.
Complete Blueprint extraction and automatic ChatGPT delivery are still pending.**

## Continue development

Start with [AGENTS.md](AGENTS.md) and [current state](docs/STATE.md). These files are
the handoff between sessions; the project does not depend on remembering this chat.

| Document | Purpose |
|---|---|
| [Current state](docs/STATE.md) | What works, what is untested, and exactly what to do next |
| [Roadmap](docs/ROADMAP.md) | Milestones and completion criteria |
| [Decisions](docs/DECISIONS.md) | Settled user requirements and architectural choices |
| [Architecture](docs/ARCHITECTURE.md) | Implemented and missing connections |
| [Blueprint discovery](docs/BLUEPRINT_DISCOVERY.md) | Plan and evidence inventory for authenticated exploration |
| [Session log](docs/SESSION_LOG.md) | Short history of completed work |
| [Browser guide](LOCAL_BROWSER.md) | Local sign-in, capture, replay, and limitations |
| [Data contract](FORMAT.md) | Normalized records accepted by the SQLite engine |

## Run on Windows

Use Python 3.10+ and your installed Chrome. From this folder in the VS Code terminal:

To get the project first:

```text
git clone https://github.com/mustafasharky/blueprint-hope.git
cd blueprint-hope
```

Then install the browser helper and start capture:

```text
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-browser.txt
.venv\Scripts\python.exe blueprint_browser.py capture
```

Sign in normally in the opened browser. Open a report, type `s` in the terminal to
save its visible text, and type `q` to finish. Future runs:

```text
.venv\Scripts\python.exe blueprint_browser.py sync
```

The launcher `run_blueprint.cmd` uses `.venv` when present and falls back to `py`.
Output is `private/blueprint_context.md`. The script currently does not transmit it.
Browser state and learner captures remain in the ignored `private/` directory.
See the browser guide before treating a replay as a complete data export.

## Offline tests and data engine

```text
py -m unittest discover -v
py study_sync.py --db private/demo.sqlite import examples/normalized_snapshot.json
py study_sync.py --db private/demo.sqlite observe examples/observation.json
py study_sync.py --db private/demo.sqlite export --out private/demo_state.json --as-of 2026-10-22T20:00:00Z
```

The examples are synthetic. A browser capture is a different format from normalized
question attempts; the mapper between them is not implemented. The standard-library
engine deduplicates imports, preserves revisions/retakes, and calculates rolling
24-hour, 7-day, and 30-day summaries.

`publish_drive.py` is an optional Google OAuth publisher for normalized JSON. Its
setup is in [optional pipeline](docs/OPTIONAL_PIPELINE.md). It is not necessary to
start browser exploration, and its live flow is not yet verified.

Coaching prompts live in `prompts/`. They are templates, not installed schedules.
The final workflow will preserve tutor memory separately from machine exports.

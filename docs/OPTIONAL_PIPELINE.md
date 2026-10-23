# Blueprint MCAT → persistent study coach

**October 23 update: local browser-session workflow added. Start with
`LOCAL_BROWSER.md` and `blueprint_browser.py`.** It opens a dedicated Chrome profile,
lets you sign in normally, captures selected visible reports, and revisits their URLs
on later runs. No platform or OAuth registration is needed for that workflow. It is
a partial capture and still needs live Blueprint mapping for complete question history.
The earlier normalized-data engine and optional Drive path below remain available;
they are not prerequisites for the browser capture.

Status: **tested offline core and an optional Google Drive publisher; not yet an
end-to-end Blueprint integration.** Created October 22, 2026.

The intended experience is: run a sync command, then open the MCAT project in ChatGPT
or receive a scheduled 5–10 minute lesson based on the latest evidence. The same
learner record also supports weekly and monthly reviews and personal context.

## What works in this starter

- Import the explicitly defined normalized JSON contract into SQLite.
- Deduplicate repeated imports; retain separate retakes and old record revisions.
- Reject mixed learner identities and conflicting changes at the same revision.
- Preserve historical results when a later capture is partial or empty.
- Keep local learning observations separate from Blueprint-owned results.
- Export current results, score history, activities, capture coverage/freshness,
  and rolling 24-hour, 7-day, 30-day, and all-time topic/skill summaries.
- Optionally upload/replace one stable, private Google Drive JSON file using
  desktop OAuth with PKCE. Tokens are kept in the operating-system keyring.
- Supply project instructions and daily/weekly/monthly coaching prompts.

Twenty tests passed for evidence handling, browser capture/filter helpers with mocked
page/response objects, and a mocked Drive create/update flow.
No live Blueprint login, live Google OAuth, live Drive upload, ChatGPT project,
tutor-memory writeback, or scheduled brief has been configured or verified.

## Optional normalized-data and Drive integration

1. A Blueprint adapter reads permitted learner performance data from the actual
   account and emits the normalized contract. The new browser helper captures raw
   visible reports; mapping complete question-level data to this contract is still pending.
2. The local sync process imports the snapshot, exports `study_state.json`, and
   replaces the content of a stable Drive file.
3. A ChatGPT project uses its Google Drive connection to read that exact file ID
   on every run, together with a separate native Google Doc for tutor memory.
4. Scheduled ChatGPT Work runs prepare the lesson. When the learner answers, the
   assistant appends observed evidence and the next review date to tutor memory.

Keep two explicit owners: the script writes machine facts; the tutor writes learning
memory. A new export must never overwrite a misconception explanation or a learner's
personal constraints. Initially the cloud memory can be a structured Google Doc with
dated evidence events. For stronger machine validation and concurrency, replace it
later with an authenticated remote MCP service exposing:

- `get_study_state(learner_id, windows)`
- `get_attempts(filters, cursor)`
- `get_learning_memory(learner_id)`
- `append_learning_event(event_id, expected_revision, event)`

That service would validate writes, deduplicate event IDs, and enforce revision checks.
It is an upgrade path, not implemented here. A public JSON URL is unnecessary.

## Blueprint browser session and optional OAuth

Blueprint's public learner documentation describes normal account sign-in and its
MCAT analytics, but the research for this starter did not locate a public OAuth client
registration or learner-export API contract. Do not invent authorization URLs, reuse
a website's internal client ID, or call this a working Blueprint OAuth integration.

Use an approved OAuth authorization-code flow with PKCE if Blueprint provides a client,
redirect URI registration, scopes, and API documentation. Otherwise, inspect the actual
signed-in MCAT account for an export or a permitted browser-based data access route.
A local interactive browser login with a saved session is a possible adapter design;
it is different from third-party OAuth and will occasionally require reauthentication.

The local browser helper now provides a first-run path without a native export or
public API. Its selected report text and value-free endpoint shapes help establish
what the complete extractor should read. An actual performance export can still be
used if available. Screenshots establish visible fields, but not API schemas.
Do not share passwords, session cookies, access tokens, or an unredacted network HAR.
If there is no export, inspect the authenticated workflow locally before writing the
adapter. See `LOCAL_BROWSER.md` for the included interactive login and capture script.

## Capture scope

| Data | Why it matters | Starter status |
|---|---|---|
| Question IDs, attempt IDs, dates, correctness | Repeated mistakes, trends, deduplication | Contract implemented; live mapping pending |
| Section, topic, reasoning skill | Diagnose the skill being tested | Contract implemented; source availability pending |
| Timing, answer changes, bookmarks | Identify patterns needing diagnosis | Optional contract fields; source mapping pending |
| Full-length and section scores | Track exam performance independently of Qbank | Contract implemented; live mapping pending |
| Module/activity completion | Context for what has been studied | Basic contract implemented; live mapping pending |
| Target score, exam date, study time | Personalize workload and urgency | Keep as explicitly reported tutor-memory context |
| Flashcard ratings and aggregate-only analytics | Extra evidence where available | Requires schema extension and verified access |
| Entire paid question/flashcard library | Not necessary for performance coaching | Not captured |

Blueprint's help article says flashcards cannot currently be exported/downloaded.
This does not prove performance metadata is unavailable; it means a blanket promise
to export everything would be inaccurate.

## Run the offline demo on Windows

Python 3.10+ is required. In VS Code's normal terminal, from this directory:

```text
py -m unittest -v
py study_sync.py --db private/demo.sqlite import examples/normalized_snapshot.json
py study_sync.py --db private/demo.sqlite observe examples/observation.json
py study_sync.py --db private/demo.sqlite export --out private/demo_state.json --as-of 2026-10-22T20:00:00Z
```

On macOS/Linux substitute `python3` for `py`. The demo is synthetic and labeled
`DEMO_ONLY`; it is not evidence about the user's MCAT performance. Use a new database
for a real learner. Do not feed synthetic records into the real study project.

`examples/demo_state.json` is the expected exported demo for inspection.
The standard-library core needs no additional packages. The import command accepts
our contract, not arbitrary Blueprint JSON, CSV, or a raw browser response.
Read `FORMAT.md` before implementing the source mapper.

## Optional Drive setup

1. Create a Google Cloud project, enable the Drive API, and configure a Desktop app
   OAuth client. For a personal external test app, configure your account as a test
   user where required. Follow Google's current consent-screen instructions.
2. Save the downloaded client JSON locally in `private/google_client.json`.
3. Use an isolated Python environment and install the optional dependencies:

```text
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-drive.txt
.venv\Scripts\python.exe publish_drive.py private/demo_state.json --client private/google_client.json --authorize --mapping private/demo_drive_mapping.json --profile demo
```

This command publishes the DEMO snapshot if you run it. Use the corresponding real
export and a separate mapping/profile when connecting a real learner.
The Google OAuth scope is `drive.file`, limited to files this app creates/opens.
The publisher does not grant sharing permissions or make the file public.
Credentials are stored through `keyring`; a working secure OS keyring is required.
The package is intended for a Windows user session; headless servers need separately
configured credential storage. Protect the local private directory with your OS user
permissions. Do not upload it or commit it to source control.

The publisher returns the Drive ID and, where available, its link. Subsequent calls
use the same mapping file and update the same Drive file. They omit `--authorize` so
an unattended job fails clearly instead of hanging at a login prompt. On expiry or
revocation, rerun interactively with `--authorize`. Google test-mode authorization
may require reauthorization; check the current OAuth configuration before relying
on unattended refreshes. Keep one publisher instance per learner, and disallow
overlapping scheduled runs.

The publisher is implemented against Google's documented client-library interfaces.
Its live authentication and upload must be tested in your account; the included
transport test is not a substitute for that. Dependencies have compatibility ranges,
not a production lockfile; lock the installed versions after live integration testing.

## Configure the ChatGPT project after live data works

Create a project for this one learner. Connect Google Drive and configure the exact
machine snapshot ID. Create a separate native Google Doc named `MCAT Tutor Memory`
and record its exact ID in project instructions. Start its sections with: learner
goals/constraints, current priorities, unresolved misconceptions, reviews due,
interventions attempted, and dated learning-event log. Unknown information stays
unknown until the learner supplies it.

Use `prompts/project_instructions.md` as the coaching instructions. Test a normal
chat reading both files and reporting the exact current `source_captured_at` and one
known recent result. Verify a follow-up observation is actually saved to the memory
document and survives a later snapshot replacement. Confirm the next chat retrieves
that observation. This checks the complete feedback loop.

Only then create scheduled runs from the prompts, with the learner's chosen timezone
and times. Test each prompt before scheduling it. Cloud schedules must use connected
sources; they cannot depend on the SQLite file sitting on your PC. A local exporter
also needs the PC on at sync time. For updates while it is off, host an authenticated
exporter after the Blueprint access method and hosting requirements are established.
Do not assume a scheduled lesson itself refreshes Blueprint.

This architecture uses connected sources in a project; it does not pretend that an
OpenAI Platform file upload updates a consumer ChatGPT Project. No public direct
Project-file-upload API was established by the documentation reviewed for this build.

## Acceptance checks before calling the system complete

- Verify Blueprint authentication and reauthentication in the chosen environment.
- Verify fields and source scope against the dashboard and one question-level report.
- Traverse pagination; preserve separate exam attempts; mark unsupported collections.
- Run the same extraction twice: no duplicate attempts, no lost memory.
- Compare a correction/retake to the old record; retain both historical evidence and
  the authoritative current value.
- Publish and confirm ChatGPT reads the newest file contents by stable ID.
- Write a tutoring observation, replace the machine snapshot, and verify it survives.
- Test an unattended brief with stale data and an expired sign-in; failures must be
  visible and should never become fabricated fresh analytics.

## Primary references checked

- Blueprint account analytics: https://help.blueprintprep.com/en/articles/9757728-mcat-lsat-account-analytics
- Blueprint MCAT flashcards/export limitation: https://help.blueprintprep.com/en/articles/5473448-mcat-flashcard-functionality
- ChatGPT projects: https://learn.chatgpt.com/docs/projects
- ChatGPT scheduled tasks: https://learn.chatgpt.com/docs/automations
- Custom MCP connections: https://learn.chatgpt.com/docs/extend/mcp
- Google desktop OAuth: https://developers.google.com/identity/protocols/oauth2/native-app
- Drive scopes: https://developers.google.com/workspace/drive/api/guides/api-specific-auth
- Drive uploads: https://developers.google.com/drive/api/guides/manage-uploads

Product capabilities depend on account/workspace availability. Recheck live
documentation when finishing integration rather than treating this research as a
guarantee about uninspected account features.

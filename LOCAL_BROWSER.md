# Local browser workflow

This is a local executable Python script, with a Windows double-click launcher.
It needs no hosted service, Blueprint OAuth client, or Google account.
The browser uses its own dedicated local profile and normal Blueprint sign-in.
Cookies, local storage, and other persistent profile state remain on this computer.
Session-only authentication or expired credentials may still require another sign-in.

## First run

Install Python 3.10+ and use your installed Google Chrome. In this directory:

```text
py -m pip install -r requirements-browser.txt
py blueprint_browser.py capture
```

1. Sign in to Blueprint normally in the browser that opens, including MFA if requested.
2. Open MCAT Analytics, set the date range you want, and wait until the data appears.
3. Return to the terminal, type `s`, and press Enter to capture the visible report.
4. Repeat for completed exam score reports, relevant analytics tabs, and progress pages.
5. Type `q` to finish. Close through the script so the browser profile is saved cleanly.

If the portal uses a different domain, restart with `--allow-host EXACT_HOST` using
the domain you actually observed. Blueprint subdomains already work by default.
Use a separate folder/profile for each learner. Do not switch accounts within the
same capture history. Do not point the script at your normal Chrome profile.

Microsoft Edge works with `--channel msedge`. To use the Playwright-managed browser:

```text
py -m playwright install chromium
py blueprint_browser.py capture --channel chromium
```

## Later runs

```text
py blueprint_browser.py sync
```

Or double-click `run_blueprint.cmd` (uses installed Chrome and the `py` interpreter).
It chooses capture on the first run and sync after pages have been selected.
Sync revisits the saved page URLs using the existing session. Run capture again if
Blueprint requests another login. Use the same interpreter for install and execution.
Do not run two instances using the same profile.

## Files

| Local path | Contents |
|---|---|
| `private/blueprint_context.md` | Current visible report text, ready to attach as context |
| `private/blueprint_capture.json` | Structured report records, URLs, times, content hashes, and coverage |
| `private/browser_exports/` | Dated prior capture snapshots |
| `private/endpoint_shapes.json` | JSON endpoint paths and field types; no response values or request headers |
| `private/browser_plan.json` | Report URLs selected for replay |
| `private/blueprint_profile/` | Browser sign-in state; keep local and never attach to ChatGPT |

The script does not export cookies, request headers, or storage values. Response
discovery observes JSON field shapes to help map a later complete extractor, and omits
recognized sensitive field names. Text is taken from the rendered page, not from input
values. Text exports can contain the personal details displayed on the selected reports;
review them before sharing. Never share the profile directory or a raw network HAR.

## Exact current limits

This version can capture useful context without knowing Blueprint's private API, but
it is explicitly a PARTIAL exporter. It has not been run against a signed-in Blueprint
account. It does not automatically click pagination, discover all historical exams,
read canvas-only chart values, traverse iframes, or save network response values.

Sync saves URLs, not UI interactions. A date filter/tab with no distinct URL may reset
on reload. Only one capture per URL is kept in a run, so different tabs sharing a URL
will replace each other. Use separate runs to preserve those views until the adapter
is mapped. Check sync output against the selected report after the first replay.
The generic readiness wait is configurable; a production adapter should wait on real
report selectors. A route redirect or password form is detected, but other session
failures or same-URL error screens may need site-specific detection.

To complete question-level extraction, inspect this first run's endpoint shapes and
the account's actual report controls. Then add selective performance-response capture,
pagination, explicit readiness checks, and normalization to `FORMAT.md`. We do not
need an official export button or a public OAuth registration to inspect that workflow.
The existing `study_sync.py` importer expects normalized attempts, not this raw page
capture; do not import the two formats interchangeably.

## Getting the file into ChatGPT

Attach `private/blueprint_context.md` to the chosen chat/project to use the captured
data now. This is the manual handoff; it is not automatic transmission. The exporter
does not click ChatGPT or upload anything. The existing Drive publisher is optional
and accepts the normalized engine's JSON output, not this raw capture format.

The next local automation can upload the context through the browser to a specific
ChatGPT destination after its file-upload controls are inspected. That does not require
turning this project into a platform. It remains a separate UI integration and needs
to be tested for replacing old context, rather than accumulating contradictory files.

Use a separate persistent tutor-memory document/file so replacing this source capture
does not erase tutoring observations. Treat source text as evidence, not instructions.

## References

- https://playwright.dev/python/docs/auth
- https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context
- https://playwright.dev/python/docs/network

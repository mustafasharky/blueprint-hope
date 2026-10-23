# Blueprint discovery checklist

Status: NOT RUN against a signed-in account. Do not fill this document from guesses.
Only commit sanitized descriptions and synthetic fixtures. Keep actual responses,
learner identifiers, question content, screenshots, and browser state under `private/`.

## First session

1. Run `blueprint_browser.py capture` locally and sign in normally.
2. Open Analytics. Record the actual portal host, UI tab names, date filters, and
   whether changing each filter changes the URL or sends a separate request.
3. Open one completed full-length score report and question review.
4. Inspect network JSON locally. Identify only requests needed for performance,
   scores, question metadata, and progress. Do not export auth responses or headers.
5. Record which requests are read-only. A POST can be a read-only query; verify its
   operation before replay. Never replay answer submissions, resets, or completion actions.
6. Follow all pages of the one report. Match exported counts to the visible totals.
7. Create a synthetic fixture with the same field structure and new fake identifiers.

The existing endpoint-shape output helps discovery but has no actual response values.
Actual JSON must be inspected locally before implementing a source mapper.

## Inventory to fill from observed evidence

| Area | Observed route / operation | Pagination / filters | Relevant fields | Coverage status |
|---|---|---|---|---|
| Analytics overview | Not inspected | Unknown | Unknown | Unknown |
| Full-length exam history | Not inspected | Unknown | Unknown | Unknown |
| Section exams | Not inspected | Unknown | Unknown | Unknown |
| Exam question results | Not inspected | Unknown | Unknown | Unknown |
| Qbank practice history | Not inspected | Unknown | Unknown | Unknown |
| Topic / reasoning skill taxonomy | Not inspected | Unknown | Unknown | Unknown |
| Modules / study progress | Not inspected | Unknown | Unknown | Unknown |
| Flashcard performance metadata | Not inspected | Unknown | Unknown | Unknown |

For each verified endpoint/operation, record the observation date, sanitized route,
HTTP method, read-only purpose, paging parameters, response shape, stable keys,
timestamp semantics, and any uncertainty. Preserve linked source-version evidence
locally without publishing credentials or personal results.

## Questions to resolve

- What uniquely identifies the learner, exam, exam attempt, question, and question attempt?
- Does timing include passage reading or just question interaction?
- How are unanswered, skipped, changed, bookmarked, or partially completed items represented?
- Are results from a retake separate records or replacements?
- What source timestamps exist for practice time versus last modification?
- Are raw topic/skill tags exposed, or only aggregate charts?
- Which fields are absent versus explicitly zero/null?
- Do history endpoints paginate, apply hidden date limits, or separate products/modes?
- What happens when a session expires? What observable signal indicates a loaded report?
- Do exports include only Blueprint work or externally imported scores too?

## First vertical slice acceptance

One completed exam is enough to start. Verify its attempt identity, section counts,
correct/incorrect/unanswered counts, available timing, score values, and topic/skill
labels. Import twice, compare the record count, and export context without new
duplicates. Only then expand to all exams and Qbank history.

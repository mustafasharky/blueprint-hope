# Roadmap

## 0. Persistent repository foundation

- [x] Preserve the existing source and synthetic examples.
- [x] Add instructions, current state, decisions, architecture, and discovery checklist.
- [x] Exclude runtime profiles, exports, credentials, and local databases.
- [ ] Publish to `mustafasharky/blueprint-hope` and verify the remote contents.

## 1. Authenticated Blueprint discovery — next

- [ ] Verify normal local browser sign-in and session reuse.
- [ ] Inventory Analytics, exam score reports, question reviews, Qbank, and study progress.
- [ ] Observe actual performance response values locally.
- [ ] Identify stable IDs, timestamps, retakes, pagination, and source scope.
- [ ] Document absent/unavailable fields and filters that lack distinct URLs.
- [ ] Commit sanitized schema notes and synthetic fixtures.

Done when one completed exam's records can be accounted for against the UI.

## 2. Reliable extraction and normalization

- [ ] Implement one complete exam-to-export vertical slice.
- [ ] Add historical exam and Qbank enumeration with pagination.
- [ ] Extend the contract only for verified source fields.
- [ ] Replace generic delays and login checks with observed readiness/error signals.
- [ ] Handle interrupted runs, session expiry, source revisions, and partial coverage.
- [ ] Verify repeated syncs do not duplicate attempts or discard learning observations.

Done when two successive live syncs agree with the source and failures preserve
the previous valid state with a visible error.

## 3. Automatic context delivery

- [ ] Select and verify a concrete ChatGPT destination.
- [ ] Implement one local sync command that extracts, normalizes, exports, and delivers.
- [ ] Verify the destination reads the new capture timestamp and known recent result.
- [ ] Replace stale context without losing learner memory.

Done when running the command updates the intended destination without a manual upload.

## 4. Persistent adaptive coaching

- [ ] Configure the separate learner-memory store and safe writeback.
- [ ] Test a daily session with real learner responses and evidence-based updates.
- [ ] Verify the observation survives a new source export and a new chat.
- [ ] Configure the user's chosen daily/weekly/monthly schedules.
- [ ] Test sparse evidence, stale data, repeat questions, and missed reviews.

Done when both the source-sync loop and the learner-feedback loop are verified.

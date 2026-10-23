# Architecture

Solid connections show implemented code paths or the manual handoff. Dashed
connections are unimplemented or not configured. Live integrations remain unverified.

```mermaid
flowchart TD
    BP["Blueprint MCAT"] --> B["Local Chrome profile + Playwright"]
    B --> R["Selected visible reports"]
    B --> E["JSON response shapes only"]
    R --> F["Markdown context + dated snapshots"]
    E -. "Map actual performance responses" .-> N["Normalized attempt JSON"]
    N --> DB["SQLite history and observations"]
    DB --> S["Study-state JSON"]
    S --> U["Optional Drive publisher"]
    F -->|"Manual attachment"| C["ChatGPT study destination"]
    U -. "Connect and validate" .-> C
    C -. "Write observed learning evidence" .-> M["Separate tutor memory"]
    M -. "Inform future lessons" .-> C
    T["Scheduled briefs"] -. "Configure after validation" .-> C
```

## Boundaries

- Browser profile: local credentials and persistent session state, never context data.
- Raw capture: visible report text and capture metadata; partial coverage is explicit.
- Normalized history: stable attempt IDs, timestamps, source revisions and typed fields.
- Export: replaceable view of source facts; not the owner of tutor memory.
- Tutor memory: learner reports and actual assessed responses, with evidence and dates.

No hosted service is required. Drive is an optional delivery mechanism. A local
browser uploader could be implemented once the actual ChatGPT destination is chosen
and its file-upload/replacement workflow is observed.

# Selected prompts, design changes, tests, and decisions — Part 3.2

Only fictional examples were used; no personal conversations or clinical records are included.

| Area | Evidence / observation | Decision / limitation |
|---|---|---|
| Scope | Part 3.1 proposed paced breathing plus STOP; Part 3.2 requires at least one completed skill. | Implement 4–6 breathing end to end first; defer STOP to Part 3.3. |
| Timing | Research R1 and Part 3.1 designed 5s introduction + 60s breathing + 5s conclusion. | Fixed 70s browser cue schedule and never require a mood entry before starting. |
| Model safety | Need to show a contribution and an outage without depending on a language model to provide crisis help. | Implement optional post-exercise context-limited chat. Store `mock`, `live`, `fallback`, or `safety` mode with each assistant message. Fixed static support page works without model. |
| Interrupted session | Closing/reloading the page during an exercise should not claim completion. | Mark the active session `interrupted` on the next successful application load. |
| Failed browser approach | On Oct 26 in the assistant's restricted sandbox, Playwright Chromium navigation to `localhost` and `file://` returned `ERR_BLOCKED_BY_ADMINISTRATOR`. This was an environment restriction, not an app HTTP failure. | Revised verification: test real FastAPI/SQLite endpoints via `pytest` and HTTP, and test the actual Vue UI with Playwright rendering plus a **mocked** HTTP transport. These are separate checks and do not establish full browser-to-backend integration. |
| Deterministic failure | `ONE_STEP_MODEL_MODE=fail` returned a recorded `fallback` assistant reply; `/support.html` returned 200 and displayed 988. | Keep the support route independent of model and continue using reproducible failure cases in future testing. |
| No user data | The app is limited to local fictional scenarios and a local SQLite database. | Ignore SQLite and API keys in Git; document no monitoring, therapy, diagnosis, or clinical validity. |

Curation note: This is a short design/test decision log, not a full AI chat export. Implementation and testing assistance from ChatGPT GPT-6 is disclosed in `AI-USE.md`.

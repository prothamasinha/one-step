# IST 402 — Assignment 3.2: Working Application and Safety

**Project:** One Step — Mental Health Skills Application (coursework prototype)  
**Student:** Prothama Sinha  
**Part:** 2 of 3 (100 points)  
**Repository:** https://github.com/prothamasinha/one-step  
**Part 1 baseline commit:** [`0d3b574`](https://github.com/prothamasinha/one-step/commit/0d3b574)  
**Part 2 submitted commit:** **[ADD THE NEW COMMIT HASH AFTER PUSHING THE PART 2 FILES]**

> **Submission check:** The Part 2 files in this draft were created and tested locally, but have **not been uploaded to the GitHub repository**. This report is **not yet ready for final Canvas submission**: upload the implementation and evidence to GitHub, confirm the links below work, insert the new commit hash, and run the application on your own machine. No completed recording or successful live-model call is claimed.

## 1. What I built for Part 2

For Part 1, I designed *One Step* around two skills, paced breathing and STOP. For this milestone I focused on making **4–6 paced breathing** work from start to finish before adding the second skill. The user can select the exercise, follow one short instruction at a time, pause, leave without penalty, and view past fictional sessions. Crisis support stays accessible through a permanent header link. There is also an optional short chat after the exercise; it is not used to control the skill.

**Implemented in the provided local draft:**

- A Vue 3 interface with a 70-second breathing flow: 5-second start instruction, six cycles of 4 seconds in and 6 seconds out (60 seconds), and a 5-second closing instruction.
- Always-available **Pause**, **Resume**, and **Leave exercise** actions; a clear message when the user chooses to leave.
- A separate static `/support.html` page describing the prototype's limits, 988 for U.S. crisis support, and emergency services. It loads without JavaScript or a model request.
- FastAPI endpoints for starting, updating, and reviewing sessions, and for saving/retrieving optional fictional chat messages.
- Local SQLite `sessions` and `messages` tables. The history screen shows the skill, timestamp, status, timing, and saved conversation.
- A constrained optional model-call path using recent fictional conversation context and an approved description of breathing. A repeatable mock reply and a deterministic failure fallback are included for tests.
- A simple-view toggle that hides extra description text without hiding the skill cue, exit controls, or crisis link.

**Not yet done:** STOP exercise, real-model call verification, a clean-checkout test on the student's computer, a genuine browser-to-localhost integration recording, and Part 3's 15-scenario evaluation. The current GitHub repository still needs the Part 2 code and evidence files.

## 2. Research findings behind the decisions

The instructor's study summary gives the relevant evidence. I used the counts as guidance about usability, **not** evidence that this app is effective for mental health treatment.

| Research finding | What I did |
|---|---|
| **R1: Short exercises** | Fixed a planned 70-second guided breathing sequence, under the 90-second course limit. |
| **R2 and D4: Crisis access** | Kept a clearly named Crisis support link in the permanent page header and created an independent static support page. |
| **R3: Permission to stop** | Offered Pause and Leave during the exercise, saving `left_early` with no negative feedback. |
| **R4: User controls the journey** | The user actively starts the skill, can leave, and can choose whether to chat or view history. |
| **D1: Less on screen** | Simple view is chosen by the user; the app does not pretend to detect distress. |
| **D2: One atomic action** | The interface shows the current inhale, exhale, or transition instruction, not a long checklist. |
| **D3: Low emotional cost** | No required mood rating, explanation, account, or chat; optional chat comes afterward. |
| **D5: Lightweight personalization** | Recent session history can offer Repeat last skill without automatically starting it. |
| **D6: Neutral language** | Short instructions, restrained colors, reduced-motion support, and no rewards or judgment labels. |

The main trade-off is scope: finishing one reliable skill with verifiable safety and persistence mattered more for Part 2 than showing two incomplete skills.

## 3. How the application works

The Vue frontend runs at `http://127.0.0.1:8000` and is served by FastAPI. Vue 3.5.13 is bundled locally so the basic interface does not need a separate build or a remote CDN. The SQLite database is created on first start and remains local. There are no accounts or real client records.

| Endpoint | Purpose |
|---|---|
| `POST /api/sessions` | Start a new breathing session. |
| `PATCH /api/sessions/{id}` | Save `completed`, `left_early`, or `interrupted`, along with measured time and user pause time. |
| `GET /api/sessions` | Show up to 40 recent fictional sessions. |
| `POST /api/chat` | Store a fictional message and respond through mock, live-model, fixed-safety, or failure-fallback mode. |
| `GET /api/messages?session_id=...` | Retrieve the saved user/assistant conversation for a session. |
| `GET /support.html` | Return static support information independently of the model. |

The app saves the selected skill, session status, start/end timestamps, actual guided time, paused time, and any optional chat messages. Assistant messages also save a `response_mode`, so a scripted mock is not confused with a real language-model reply. This supports a basic history and repeat option without collecting real mental-health data.

## 4. Timing: expected and observed

The intended guided experience starts when the first exercise instruction appears. Entry/setup and the API call to create the session happen **before** the timing begins. The clock excludes voluntary pauses but counts ordinary application elapsed time; opening crisis support does not force exercise completion.

| Stage | Intended time |
|---|---:|
| First instruction | 5 seconds |
| Six rounds: inhale 4 seconds, exhale 6 seconds | 60 seconds |
| Closing instruction | 5 seconds |
| **Total** | **70 seconds** |

Two Playwright checks of the actual Vue UI used **mocked HTTP**. An accelerated browser clock reached the completion screen at a displayed **70 seconds**; a separate real wall-clock browser run measured **70.24 seconds from the first visible exercise instruction to the visible completion screen**, with no user pauses (`evidence/real-timing-results.json`). These measurements support the chosen 70-second guided pace, but neither is a real-person usability study or a fully connected browser-to-backend test. The backend separately stored a **70.02-second** fictional session supplied in an HTTP test; that value verifies database persistence, not a measured user exercise.

**Assumption:** a fictional user follows the fixed paced cues without pausing. If they pause or leave, the app respects that choice and does not force them back into the sequence.

## 5. Model contribution and safety boundaries

The model is **optional and post-exercise only**. The FastAPI prompt supplies the fixed approved breathing description, the current fictional interaction, and a short recent conversation. Its job is limited to a brief acknowledgment and mention of existing app choices. The **Vue application, not the model**, controls breathing instructions, timing, leaving, saved session state, and the Crisis support route. I did not use the model to invent therapeutic instructions or decide whether a user can see resources.

For repeatable testing, the default `ONE_STEP_MODEL_MODE=mock` gives a labeled scripted response. With `ONE_STEP_MODEL_MODE=fail`, a simulated outage produces a fixed fallback message. Source code also supports an optional `live` OpenAI Responses API request when a key is supplied; **I have not successfully verified a live API response in this draft**. Basic crisis-related keywords trigger fixed prototype wording, but this rule is **not a risk detector**: it can miss indirect language or flag a benign phrase. It never controls the static crisis-support page.

This is not a diagnostic, therapy, crisis, or monitored service. Only fictional messages are allowed in testing. Nobody should rely on this coursework prototype for real support.

## 6. Verification evidence: what was actually checked

The following checks were performed in the local drafting environment on **October 26, 2026**. These results are not claims of deployment or clinical efficacy.

| Check | Expected result | Observed result and evidence |
|---|---|---|
| Automated API checks | Session state, chat history, failures, support page, and validation work | **12/12 pytest checks passed**, `evidence/pytest-results.txt`. |
| Actual FastAPI / SQLite request check | Session and messages persist; support route works after failed model | Saved `completed` breathing session with test-supplied `70.02` seconds, then saved user + assistant rows with `fallback` mode. `/support.html` returned HTTP 200 with 988. `evidence/backend-http-and-sqlite.json`. |
| Vue screen checks with mocked HTTP | Home, exit, history, fallback, and static crisis information appear | **7/7 browser presentation and behavior checks passed**. `evidence/browser-results.json` and screenshots. |
| 70-second UI and wall-clock timing | Complete within the intended 90-second limit | Virtual-clock run displayed 70 seconds; **real wall-clock mocked-transport run measured 70.24 seconds** to completion. `evidence/real-timing-results.json` and the two completion screenshots. |
| Leaving early | User may leave without explaining | Exit screen showed “You chose to stop”; backend independently verified `left_early` state. |
| Model failure | Chat shows fallback, crisis route stays usable | Failed-mode backend test returned `fallback`; Vue mocked-failure screen kept Crisis support visible. |
| Interrupted session | No false completion after refresh | Backend `interrupted` status test passed; genuine browser-to-backend refresh integration still needs manual checking. |

**Important testing distinction:** direct browser navigation to the local server was blocked by `ERR_BLOCKED_BY_ADMINISTRATOR` in the sandbox. Instead of calling that a passing integrated test, I tested the **real** FastAPI and SQLite backend with pytest/HTTP, and the **real Vue screen logic** with a Playwright-injected **mock HTTP transport**. The browser screenshots show mocked-transport runs, not a fully connected browser session. I still need to verify the complete browser-to-backend workflow locally before final submission.

## 7. Failure, revision, and what I learned

One failed approach was trying to test the local browser and backend through normal Playwright navigation. The test environment blocked both `http://localhost` and local file navigation, even though direct Python HTTP requests to FastAPI worked. I changed the verification approach instead of treating the failed browser launch as an application defect. The new approach separated backend persistence and failure tests from mocked UI checks. This made the evidence repeatable but left a clear integration gap for the next verification pass.

Another deliberate decision was leaving STOP unfinished for now. The course asks for at least one complete skill at this milestone, and the research emphasizes short, simple interactions. I prioritized an end-to-end breathing sequence, user control, saved history, and safety independence.

## 8. Repository, design, verification, and recording links

**Repository (currently contains the Part 1 design only):** https://github.com/prothamasinha/one-step  
**Part 1 design:** [Research, flow, wireframe, and proposed architecture](https://github.com/prothamasinha/one-step/blob/main/report%20%283%29.md)  
**Part 2 submitted commit:** **[REPLACE WITH NEW COMMIT URL]**  
**Part 2 code and run instructions (links work after push):** [README](https://github.com/prothamasinha/one-step/blob/main/README.md) · [FastAPI](https://github.com/prothamasinha/one-step/blob/main/backend/app.py) · [Vue](https://github.com/prothamasinha/one-step/blob/main/frontend/app.js)  
**Verification evidence (links work after push):** [test results](https://github.com/prothamasinha/one-step/blob/main/evidence/pytest-results.txt) · [real backend/SQLite results](https://github.com/prothamasinha/one-step/blob/main/evidence/backend-http-and-sqlite.json) · [browser results](https://github.com/prothamasinha/one-step/blob/main/evidence/browser-results.json) · [wall-clock timing](https://github.com/prothamasinha/one-step/blob/main/evidence/real-timing-results.json) · [screenshots](https://github.com/prothamasinha/one-step/tree/main/evidence) · [decision log](https://github.com/prothamasinha/one-step/blob/main/evidence/decision-log.md)  
**AI-use disclosure (after push):** [AI-USE.md](https://github.com/prothamasinha/one-step/blob/main/AI-USE.md)  
**Recording:** Not yet created. A student-recorded local demo showing the actual app, session database, interrupted flow, and failure is recommended before final submission; the finished-app screencast is required for Part 3.3.

## 9. Remaining work

Before submitting this Part 2 report, I need to upload the project and evidence to GitHub, add the exact submitted commit hash, verify the absolute links, and run the complete frontend/backend app on my own machine. I also need to check the actual browser timing and include a short real integrated demonstration if available. For Part 3.3 I will complete or explicitly re-scope STOP, review saved-history personalization, run at least 15 fictional scenarios and three behavior checks, repeat selected live-model cases if configured, and record the debugging screencast required by the overview.

**AI disclosure:** ChatGPT / OpenAI GPT-6 assisted with the implementation draft, testing scripts, and report organization. Vue 3.5.13 is bundled under its MIT license. No live-model call or real-person clinical test is claimed. Details appear in `AI-USE.md`.

**Reference:** Penn State IST 402. (2026). *Assignment 3 overview: Mental Health Skills Application*, Sections 2–8. https://psu.instructure.com/courses/2484533/pages/assignment-3-overview-mental-health-skills-application

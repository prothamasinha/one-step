# Verify this Part 2 draft before uploading `report.md`

These instructions use fictional content only.

1. From the project root, install the Python dependencies and run the server as shown in `README.md`.
2. Open `http://127.0.0.1:8000` in your browser. Complete a 70-second practice and confirm the completion screen. Take a screenshot of the final cue and completion summary; measure actual wall time separately from entry/setup.
3. Start again, press **Leave exercise**, then open **Review history**. Confirm the status `left_early` and open the saved chat.
4. Run `ONE_STEP_MODEL_MODE=fail python -m uvicorn backend.app:app --port 8000`, finish or leave an exercise, and send a clearly labeled **fictional** message. Confirm `fallback` appears. Then click Crisis support and verify the static page opens.
5. Inspect SQLite using `sqlite3 one_step.sqlite3 "SELECT id,skill_type,status,actual_exercise_seconds FROM sessions;"` and `sqlite3 one_step.sqlite3 "SELECT session_id,role,response_mode FROM messages;"`.
6. Run `python -m pytest tests -q`. Keep any screenshots/logs redacted and do not commit `*.sqlite3` or secret keys.
7. Upload the whole project (not the local SQLite database) to GitHub, then replace the Part 2 commit placeholder in `report.md` with the *new* GitHub SHA and confirm every evidence link resolves before uploading exactly `report.md` to Canvas.

Testing environment note: the assistant's sandbox blocked Playwright navigations to localhost. The screenshots labeled `mocked` are genuine Chromium renderings of the Vue UI with a mocked transport; they are **not** evidence of real UI-to-server integration. API/SQLite requests and tests ran against actual FastAPI routes separately.

# Part 2 verification notes (fictional scenarios only)

| Check | Expected | Evidence |
|---|---|---|
| Complete 4–6 breathing | Six inhale/exhale cycles, fixed 70-second sequence, `completed` SQLite record | Browser timing log, screenshot, database query |
| Leave early | Return to completion/exit screen without shame or penalty; `left_early` stored | API test and browser screenshot |
| Model fails | `fallback` reply recorded; crisis link stays usable | API test and browser screenshot |
| Crisis support | Direct `/support.html` works without model, even after failure | API test, direct HTTP and screenshot |
| Chat persistence | User and assistant turns readable for a saved session | API test and SQLite query |
| Refresh interruption | Previously active session marked `interrupted` after reload | Browser test, SQLite query |

The reproducible mock test suite does not establish clinical effectiveness. Student should verify screenshots and timings in their own setup and upload the artifact commit to GitHub before Canvas submission.

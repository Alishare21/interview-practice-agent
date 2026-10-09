# Interview Practice Agent audit

**Date:** 2026-10-09
**Scope:** local workflow, hosted chat app, rubric calculation, append-only attempt logging, progress reports, résumé topic coverage, downloadable PDF, and clean-checkout readiness.

## Result

The helper workflow passed its focused automated checks. After that audit snapshot, a six-question live practice run was completed and its report was rendered as a four-page PDF and visually inspected. Its six local entries and generated report are private and excluded from the public repository. Test examples below are fictional; the later live results are kept locally only.

| Check | Evidence | Result |
|---|---|---|
| Question bank | Six topics and twelve questions load and select | Pass |
| Weighted scoring | The supplied rubric example `4,4,3,4,3` calculates to `3.6 / 5` | Pass |
| Strong answer scenario | Scores `5,5,5,5,4` calculate to `4.9 / 5`, Excellent | Pass |
| Incorrect method scenario | Scores `1,2,1,3,1` calculate to `1.4 / 5`, Needs work | Pass |
| Adaptive selection | Two scores of at least 4.0 move the target up one level | Pass |
| Seven-day repeat guard | A recently skipped question is excluded from a new selection | Pass |
| Logging privacy | With `store_answers: false`, a supplied full answer is omitted from the JSONL entry | Pass |
| Corrections | Original line remains; a correction line supersedes it in progress summaries | Pass |
| Fresh clone | `init` creates local profile and empty log; selection, scoring, recording, and summaries then run | Pass |
| Export and deletion | Export matches the log; deletion refuses anything other than explicit `YES` | Pass |
| Question-level review | A weak sample retains the specific wrong step and exposes its lowest rubric dimensions in the session summary | Pass |
| End-of-interview report | Strong and incorrect sample answers appear in separate groups with the question, specific feedback, and score-based weak points | Pass |
| Custom topic | A generated business-analysis question is scored and included in the wrong-answer report without storing the answer or résumé | Pass |
| PDF report | A six-question session generated a four-page professional PDF with score tables, question reviews, explanations, and example answers; rendered pages were visually checked | Pass |
| Automated suite | `python -m unittest discover -s tests -v`: thirteen tests passed | Pass |
| Practice log privacy | Live session answers are omitted by default; the log is excluded from the public repository | Pass |
| Web startup | Streamlit AppTest starts the app, shows the missing-secret message without an unhandled exception, and reaches the login form with test-only environment values | Pass |
| Chat transcript | Clean Git checkout launches the chat flow, records a skip, advances to the next question, and finishes a two-question test round | Pass |
| Automatic PDF delivery | Final skipped sample answer immediately creates a PDF download button in the clean checkout | Pass |
| PDF content | Extracted test PDF text contains the answer, five rubric scores, correction, example answer, strengths, and next-practice guidance | Pass |
| Scoring integration | Isolated mocked AI response flows through the website scorer, computes 3.6/5 with the project helper, appends one scored attempt, and omits the full answer | Pass |
| API quota error UX | Exhausted-credit responses show a short billing explanation; raw provider details are not displayed | Pass |
| Resume topic coverage | Optional résumé skill extraction adds explicit topics to the round; capped at 40 total topics so the required two-per-topic plan stays within 80 questions | Code-reviewed; live model response still requires the owner's API key |
| Hosted deployment | No API key, shared password, or hosting account credentials are available in this workspace; no deployment URL was created | Blocked on owner secrets and hosting setup |

For the incorrect-method scenario, the fictional response was: “Sort the list and return the positions of two numbers that look closest.” It does not establish the target sum and can lose the original indices. The low relevance and depth scores are based on those defects. A wrong method is scored honestly; it is logged as `skipped` only when the candidate chooses to skip.

## Level-up completed

The local version is now complemented by a Streamlit web app with a chat transcript and commands for hint, skip, retry, model answer, next, progress, topics, end, and help. It asks for familiar topics and an optional résumé, extracts explicit résumé skill areas into the question plan, rotates topics, uses adaptive question difficulty, and generates the downloadable professional PDF automatically when the planned last answer or skip is recorded. The report content has an automated PDF text check. A clean-checkout smoke test verifies chat progression and PDF availability without changing the real practice log.

## Limits

The current intake accepts any candidate topic and an optional résumé. The starter bank remains available as a fallback. Generated questions and their checklists are saved with the attempt so the report can name them; résumé text and full answers stay out of the log by default. The custom-topic path is tested with a business-analysis scenario, but the quality of generated questions across arbitrary subjects still requires human review. The shared hosted password is a basic demo gate, not individual user accounts. Hosted filesystem contents can reset when the service restarts, so users must download each report.

- The Python helper verifies arithmetic, file behavior, selection, and summaries. The conversational coach still judges the five rubric dimensions against the candidate's actual answer; that judgment needs review with real practice answers over time.
- No hiring outcome or company-specific interview pattern is inferred from these tests.
- The public repository excludes the local AIS-OS installation, personal profile, real attempt log, generated student PDF reports, and private audit history.

## Next live check

The code is ready for the configured Streamlit Community Cloud deployment path. Before a public URL can be tested, the repository owner must set a real API key and shared demo password in hosting secrets, select the repository and `web_app.py` entry point, and deploy. No live model scoring run or hosted deployment has been claimed in this audit.

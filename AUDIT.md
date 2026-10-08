# Interview Practice Agent audit

**Date:** 2026-10-08  
**Scope:** local question bank, rubric calculation, attempt logging, progress reports, fresh-clone setup, and public repository readiness.

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
| Automated suite | `python -m unittest discover -s tests -v`: nine tests passed | Pass |
| Practice log privacy | Live session answers are omitted by default; the log is excluded from the public repository | Pass |

For the incorrect-method scenario, the fictional response was: “Sort the list and return the positions of two numbers that look closest.” It does not establish the target sum and can lose the original indices. The low relevance and depth scores are based on those defects. A wrong method is scored honestly; it is logged as `skipped` only when the candidate chooses to skip.

## Level-up completed

The first version required local `profile.yaml` and `progress_log.jsonl` but excluded them from Git, so a public clone would be incomplete. `profile.example.yaml` and the `init` command now create both private files without overwriting existing practice data. The fresh-clone test covers that setup and one full sample attempt. The session summary now exposes question-by-question feedback, rubric-based answer groups, and weak dimensions, so a candidate can see exactly what to fix after the interview. The skill generates this report automatically after the requested number of questions.

## Limits

The current intake accepts any candidate topic and an optional résumé. The starter bank remains available as a fallback. Generated questions and their checklists are saved with the attempt so the report can name them; résumé text and full answers stay out of the log by default. The custom-topic path is tested with a business-analysis scenario, but the quality of generated questions across arbitrary subjects still requires human review.

- The Python helper verifies arithmetic, file behavior, selection, and summaries. The conversational coach still judges the five rubric dimensions against the candidate's actual answer; that judgment needs review with real practice answers over time.
- No hiring outcome or company-specific interview pattern is inferred from these tests.
- The public repository excludes the local AIS-OS installation, personal profile, real attempt log, generated student PDF reports, and private audit history. The published coach runs in Codex; the Python helper alone is not a conversational app.

## Next live check

Continue with another custom topic or use the starter bank. Confirm each completed session creates a separate professional PDF and that student reports remain excluded from the public repository.

# Interview Practice Agent

A general interview practice coach. It first asks which topics the student knows and invites an optional résumé, then asks questions on those topics and relevant résumé experience. It scores each answer with a fixed rubric, gives short feedback, and records attempts so progress can be reviewed. It is a practice partner, not a real interviewer or a hiring predictor.

## Set up

Requires Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
python src/interview_log.py init
```

The `init` command creates a private `profile.yaml` from [profile.example.yaml](profile.example.yaml) and an empty `progress_log.jsonl`. It reports what it created and does not overwrite either file. Both local files are excluded from Git.

Open this folder in Codex and say **“start”**. Name any topic you want to practise, such as business analysis, design, finance, or software. You can also share a résumé; the coach uses it to tailor questions and add explicit skill areas to the question plan without saving résumé text in the practice log. If you give no topic, the bundled starter questions are available. The default session has at least ten questions and expands to cover each selected or résumé-derived topic twice. If you enter a different question count, the session uses that exact count. It rotates across topics and uses adaptive difficulty. The commands are `hint`, `skip`, `retry`, `model answer`, `progress`, `topics`, `end`, and `delete log`.

The [interview-practice skill](.agents/skills/interview-practice/SKILL.md) defines the local coach's behavior. [Interview agent specification](interview_agent_spec.md) preserves the supplied rules. `web_app.py` is a standalone web version for live interviews, AI scoring, and downloadable PDF reviews. The local Codex workflow remains available for private practice.

## Run the web app locally

```bash
python -m pip install -r requirements.txt
streamlit run web_app.py
```

The live AI workflow needs either a Groq API key or an OpenAI API key, plus an app password. Groq is preferred when `GROQ_API_KEY` is configured; its free plan is rate-limited and uses a different model from OpenAI. Set `GROQ_API_KEY` and `APP_PASSWORD` in your environment for local use, or set `OPENAI_API_KEY` to use OpenAI instead. The app sends topics, optional résumé text, and interview answers to the configured AI provider to generate questions and feedback. The chat transcript and report are held in the active browser session; structured scores and brief feedback are appended to the project log. Full answers are excluded from that log unless `profile.yaml` opts in. On a hosted demo, do not enter sensitive résumé or interview information. Never commit an API key, app password, or a student's report to GitHub.

The hosted app uses a shared demo password, not individual student accounts. Everyone with that password shares the app's progress log and can use its export and delete controls. The host's local files may be reset when the app restarts, so download each PDF when it appears.

## Publish a live demo URL

The app is prepared for [Streamlit Community Cloud](https://share.streamlit.io/):

1. Push this project to a GitHub repository you administer.
2. Sign in to Streamlit Community Cloud with GitHub and choose **Create app**.
3. Select the repository and branch, and set the app file to `web_app.py`.
4. In **Advanced settings → Secrets**, add `GROQ_API_KEY = "your-key"` and `APP_PASSWORD = "a-long-random-password"`, then save. Create the Groq key in the GroqCloud Console. The account owner must be 18 or older. Groq's free tier has rate limits, and Groq may temporarily retain request content for reliability or abuse investigations. Keep both values in hosting secrets; do not put them in GitHub or paste the API key into chat. To use OpenAI instead, configure `OPENAI_API_KEY` in place of `GROQ_API_KEY`.
5. Deploy and share the generated `https://…streamlit.app` URL and the app password with your teacher.

Community Cloud requires access to the GitHub repository and installs packages from `requirements.txt`. The host may pause an idle demo, so open the link and allow it to wake before presenting. See [Streamlit's deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app) and [secrets guide](https://docs.streamlit.io/deploy/concepts/secrets).

## Files

| File | Purpose |
|---|---|
| [topics.yaml](topics.yaml) | Twelve optional starter questions across software, SQL, data quality, statistics, and behavioral topics |
| [rubric.md](rubric.md) | Fixed five-dimension weighted scoring rubric |
| [profile.example.yaml](profile.example.yaml) | Default local profile; full answer storage is off |
| [src/interview_log.py](src/interview_log.py) | Question selection, weighted totals, append verification, summaries, export, and deletion |
| [src/report_pdf.py](src/report_pdf.py) | Professional PDF report generation for a completed session |
| [tests/test_interview_log.py](tests/test_interview_log.py) | Focused checks using isolated test logs |
| [AUDIT.md](AUDIT.md) | Current functional verification and limitations |

The question bank and rubric are read-only during practice. The user's full answers are stored only when they explicitly change `store_answers` to true in their local profile. The log is append-only except for a confirmed deletion request.

After the final question, the web coach offers a downloadable professional PDF review; the local workflow saves it in `output/pdf/`. The full review includes each question and candidate answer, each attempt's result and five rubric scores, what was correct or needs correction, plain-language explanations, example improved answers, demonstrated knowledge, strengths, weak points, topics to revisit, and a focused next-practice exercise. During the interview, the website behaves as a chat: answer in the chat box and type `hint`, `skip`, `retry`, `model answer`, `next`, `progress`, `topics`, `end`, or `help` as needed. Detailed scoring is saved for the final report.

## Recent update: any interview topic

- At the start, the coach asks which topics the student is familiar with and invites an optional résumé.
- It can create questions for a topic outside the starter bank, including questions based on skills or projects the student actually supplied.
- Each custom question keeps its question text and assessment checklist in the practice log, so the final report can identify it. The résumé and full answer are not saved by default.
- The same rubric and end-of-interview report apply to starter and custom questions. During the interview, answers are logged with only a brief acknowledgment; the report at the end provides scores, correct and incorrect answers, supported strengths, weak points, and a next exercise.
- The functional suite includes custom-topic reporting and privacy checks. Generated question quality still needs review during real practice.
- The standard round stops after its planned questions so the student gets a focused report. The default plan expands for topic coverage; a different number selected at intake is the exact session length. They can choose another round afterward. Detailed feedback is held until the report, which explains why wrong answers missed the mark and shows a concise improved example.
- `src/report_pdf.py` creates the formatted PDF from the session log and coach-written notes. Each completed interview gets a separate PDF named for its session. Student reports are saved locally and excluded from Git so personal practice details do not become public. Reports contain learning feedback, not a hiring prediction.
- The web app includes the same chat-style interview controls and creates a downloadable report at completion. Its shared demo password is an access gate, not individual accounts; do not use the public demo for sensitive personal data.

## Verify

```bash
python -m unittest discover -s tests -v
python src/interview_log.py progress
python src/report_pdf.py --session-id YOUR-SESSION-ID
```

The tests do not write to the real practice log. They check scoring math, question selection, private answer handling, corrections, export and deletion safeguards, and a clean setup through a completed sample attempt.

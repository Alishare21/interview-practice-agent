# Interview Practice Agent

A general interview practice coach. It first asks which topics the student knows and invites an optional résumé, then asks questions on those topics and relevant résumé experience. It scores each answer with a fixed rubric, gives short feedback, and records attempts so progress can be reviewed. It is a practice partner, not a real interviewer or a hiring predictor.

## Set up

Requires Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
python src/interview_log.py init
```

The `init` command creates a private `profile.yaml` from [profile.example.yaml](profile.example.yaml) and an empty `progress_log.jsonl`. It reports what it created and does not overwrite either file. Both local files are excluded from Git.

Open this folder in Codex and say **“start”**. Name any topic you want to practise, such as business analysis, design, finance, or software. You can also share a résumé; the coach uses it to tailor questions without saving its text in the practice log. If you give no topic, the bundled starter questions are available. A session defaults to at least three questions per named topic, with a minimum of five total, and adaptive difficulty. You can choose a different count. The commands are `hint`, `skip`, `retry`, `model answer`, `progress`, `topics`, `end`, and `delete log`.

The [interview-practice skill](.agents/skills/interview-practice/SKILL.md) defines the coach's behavior. [Interview agent specification](interview_agent_spec.md) preserves the supplied rules. This is a Codex skill with a Python scoring and logging helper; it is not a standalone web app.

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

After the final question, the coach generates a professional PDF review in `output/pdf/`. The full review is delivered in PDF format and includes each question and score, what was answered correctly or needs correction, plain-language explanations, example improved answers, topics to revisit, and the student's supported strengths and weak points. The conversation gives the student the PDF location.

## Recent update: any interview topic

- At the start, the coach asks which topics the student is familiar with and invites an optional résumé.
- It can create questions for a topic outside the starter bank, including questions based on skills or projects the student actually supplied.
- Each custom question keeps its question text and assessment checklist in the practice log, so the final report can identify it. The résumé and full answer are not saved by default.
- The same rubric and end-of-interview report apply to starter and custom questions. During the interview, answers are logged with only a brief acknowledgment; the report at the end provides scores, correct and incorrect answers, supported strengths, weak points, and a next exercise.
- The functional suite now includes a custom-topic reporting and privacy check; all nine tests pass. Generated question quality still needs review during real practice.
- The standard round stops after its planned questions so the student gets a focused report. They can choose another round afterward. Detailed feedback is held until the report, which explains why wrong answers missed the mark and shows a concise improved example.
- `src/report_pdf.py` creates the formatted PDF from the session log and coach-written notes. Each completed interview gets a separate PDF named for its session. Student reports are saved locally and excluded from Git so personal practice details do not become public. Reports contain learning feedback, not a hiring prediction.

## Verify

```bash
python -m unittest discover -s tests -v
python src/interview_log.py progress
python src/report_pdf.py --session-id YOUR-SESSION-ID
```

The tests do not write to the real practice log. They check scoring math, question selection, private answer handling, corrections, export and deletion safeguards, and a clean setup through a completed sample attempt.

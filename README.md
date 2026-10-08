# Interview Practice Agent

A general interview practice coach. It first asks which topics the student knows and invites an optional résumé, then asks questions on those topics and relevant résumé experience. It scores each answer with a fixed rubric, gives short feedback, and records attempts so progress can be reviewed. It is a practice partner, not a real interviewer or a hiring predictor.

## Set up

Requires Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
python src/interview_log.py init
```

The `init` command creates a private `profile.yaml` from [profile.example.yaml](profile.example.yaml) and an empty `progress_log.jsonl`. It reports what it created and does not overwrite either file. Both local files are excluded from Git.

Open this folder in Codex and say **“start”**. Name any topic you want to practise, such as business analysis, design, finance, or software. You can also share a résumé; the coach uses it to tailor questions without saving its text in the practice log. If you give no topic, the bundled starter questions are available. A session defaults to five questions and adaptive difficulty. The commands are `hint`, `skip`, `retry`, `model answer`, `progress`, `topics`, `end`, and `delete log`.

The [interview-practice skill](.agents/skills/interview-practice/SKILL.md) defines the coach's behavior. [Interview agent specification](interview_agent_spec.md) preserves the supplied rules. This is a Codex skill with a Python scoring and logging helper; it is not a standalone web app.

## Files

| File | Purpose |
|---|---|
| [topics.yaml](topics.yaml) | Twelve optional starter questions across software, SQL, data quality, statistics, and behavioral topics |
| [rubric.md](rubric.md) | Fixed five-dimension weighted scoring rubric |
| [profile.example.yaml](profile.example.yaml) | Default local profile; full answer storage is off |
| [src/interview_log.py](src/interview_log.py) | Question selection, weighted totals, append verification, summaries, export, and deletion |
| [tests/test_interview_log.py](tests/test_interview_log.py) | Focused checks using isolated test logs |
| [AUDIT.md](AUDIT.md) | Current functional verification and limitations |

The question bank and rubric are read-only during practice. The user's full answers are stored only when they explicitly change `store_answers` to true in their local profile. The log is append-only except for a confirmed deletion request.

After the final question, the coach shows every question with its score and feedback, groups correct, partly correct, and incorrect technical answers, and summarizes demonstrated knowledge and weak points. The labels follow the relevance rubric score and can be reviewed against the actual answer. Behavioral answers are described as strong, developing, or needing work.

## Recent update: any interview topic

- At the start, the coach asks which topics the student is familiar with and invites an optional résumé.
- It can create questions for a topic outside the starter bank, including questions based on skills or projects the student actually supplied.
- Each custom question keeps its question text and assessment checklist in the practice log, so the final report can identify it. The résumé and full answer are not saved by default.
- The same rubric and end-of-interview report apply to starter and custom questions. The report lists correct, partly correct, and incorrect answers, plus supported strengths, weak points, and a next exercise.
- The functional suite now includes a custom-topic reporting and privacy check; all nine tests pass. Generated question quality still needs review during real practice.

## Verify

```bash
python -m unittest discover -s tests -v
python src/interview_log.py progress
```

The tests do not write to the real practice log. They check scoring math, question selection, private answer handling, corrections, export and deletion safeguards, and a clean setup through a completed sample attempt.

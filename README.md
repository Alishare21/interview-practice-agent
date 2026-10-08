# Interview Practice Agent

A local interview practice coach for general software and data roles. It asks one question at a time, scores each answer with a fixed rubric, gives short feedback, and records attempts so progress can be reviewed. It is a practice partner, not a real interviewer or a hiring predictor.

## Set up

Requires Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
python src/interview_log.py init
```

The `init` command creates a private `profile.yaml` from [profile.example.yaml](profile.example.yaml) and an empty `progress_log.jsonl`. It reports what it created and does not overwrite either file. Both local files are excluded from Git.

Open this folder in Codex and say **“start”** or **“start sql-analytics”**. A session defaults to five questions and adaptive difficulty. The commands are `hint`, `skip`, `retry`, `model answer`, `progress`, `topics`, `end`, and `delete log`.

The [interview-practice skill](.agents/skills/interview-practice/SKILL.md) defines the coach's behavior. [Interview agent specification](interview_agent_spec.md) preserves the supplied rules. This is a Codex skill with a Python scoring and logging helper; it is not a standalone web app.

## Files

| File | Purpose |
|---|---|
| [topics.yaml](topics.yaml) | Twelve starter questions across software, SQL, data quality, statistics, and behavioral topics |
| [rubric.md](rubric.md) | Fixed five-dimension weighted scoring rubric |
| [profile.example.yaml](profile.example.yaml) | Default local profile; full answer storage is off |
| [src/interview_log.py](src/interview_log.py) | Question selection, weighted totals, append verification, summaries, export, and deletion |
| [tests/test_interview_log.py](tests/test_interview_log.py) | Focused checks using isolated test logs |
| [AUDIT.md](AUDIT.md) | Current functional verification and limitations |

The question bank and rubric are read-only during practice. The user's full answers are stored only when they explicitly change `store_answers` to true in their local profile. The log is append-only except for a confirmed deletion request.

After the final question, the coach shows every question with its score and feedback, groups correct, partly correct, and incorrect technical answers, and summarizes demonstrated knowledge and weak points. The labels follow the relevance rubric score and can be reviewed against the actual answer. Behavioral answers are described as strong, developing, or needing work.

## Verify

```bash
python -m unittest discover -s tests -v
python src/interview_log.py progress
```

The tests do not write to the real practice log. They check scoring math, question selection, private answer handling, corrections, export and deletion safeguards, and a clean setup through a completed sample attempt.

"""Deterministic storage and reporting for the interview practice skill."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = ("relevance", "structure", "depth", "communication", "impact")
WEIGHTS = {"relevance": Decimal("0.30"), "structure": Decimal("0.25"),
           "depth": Decimal("0.25"), "communication": Decimal("0.10"),
           "impact": Decimal("0.10")}
DIFFICULTIES = ("easy", "medium", "hard")
IST = timezone(timedelta(hours=5, minutes=30))


def read_yaml(name: str) -> dict:
    path = ROOT / name
    if not path.exists():
        raise ValueError(f"Missing {name}; create a sensible default before continuing.")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{name} must contain a YAML mapping")
    return data


def load_bank() -> tuple[dict, dict]:
    topics = read_yaml("topics.yaml").get("topics")
    if not isinstance(topics, list) or not topics:
        raise ValueError("topics.yaml has no topics")
    topic_map, question_map = {}, {}
    for topic in topics:
        if not isinstance(topic, dict) or not isinstance(topic.get("id"), str):
            raise ValueError("Every topic needs an id")
        tid = topic["id"]
        if tid in topic_map or topic.get("difficulty") not in DIFFICULTIES:
            raise ValueError(f"Duplicate topic or invalid difficulty: {tid}")
        topic_map[tid] = topic
        for question in topic.get("questions", []):
            if not isinstance(question, dict) or not isinstance(question.get("id"), str):
                raise ValueError(f"Invalid question in {tid}")
            qid = question["id"]
            if qid in question_map or not question.get("text") or not question.get("ideal_points"):
                raise ValueError(f"Duplicate or incomplete question: {qid}")
            question_map[qid] = (tid, question)
    return topic_map, question_map


def load_profile() -> dict:
    profile = read_yaml("profile.yaml")
    if not isinstance(profile.get("store_answers"), bool):
        raise ValueError("profile.yaml needs a boolean store_answers")
    if not isinstance(profile.get("topics", []), list):
        raise ValueError("profile.yaml topics must be a list")
    return profile


def initialize() -> dict:
    """Create private local state from the public example without overwriting it."""
    load_bank()
    if not (ROOT / "rubric.md").is_file():
        raise ValueError("Missing rubric.md; restore the public rubric before continuing.")
    example = ROOT / "profile.example.yaml"
    if not example.is_file():
        raise ValueError("Missing profile.example.yaml; restore the public example before continuing.")
    created = []
    profile = ROOT / "profile.yaml"
    if not profile.exists():
        with profile.open("x", encoding="utf-8") as handle:
            handle.write(example.read_text(encoding="utf-8"))
        created.append("profile.yaml from profile.example.yaml")
    load_profile()
    log = ROOT / "progress_log.jsonl"
    if not log.exists():
        log.touch(exist_ok=False)
        created.append("empty progress_log.jsonl")
    load_log()
    return {"created": created, "message": "Local practice files are ready."}


def load_log() -> list[dict]:
    path = ROOT / "progress_log.jsonl"
    if not path.exists():
        raise ValueError("Missing progress_log.jsonl; create an empty log before continuing.")
    entries = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid log JSON on line {line_number}: {exc}") from exc
        if not isinstance(entry, dict):
            raise ValueError(f"Invalid log entry on line {line_number}")
        entries.append(entry)
    return entries


def overall(scores: dict) -> float:
    if set(scores) != set(DIMENSIONS):
        raise ValueError("Scores must include exactly the five rubric dimensions")
    if any(type(scores[key]) is not int or not 1 <= scores[key] <= 5 for key in DIMENSIONS):
        raise ValueError("Each dimension score must be a whole number from 1 to 5")
    value = sum(Decimal(scores[key]) * WEIGHTS[key] for key in DIMENSIONS)
    return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_EVEN))


def band(value: float) -> str:
    return "Excellent" if value >= 4.5 else "Strong" if value >= 3.5 else "Developing" if value >= 2.5 else "Needs work"


def record(input_path: Path) -> dict:
    raw = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Record input must be a JSON object")
    allowed = {"session_id", "topic_id", "question_id", "difficulty", "status", "scores",
               "hint_used", "feedback_summary", "answer", "corrects", "question_text",
               "ideal_points", "category"}
    extra = set(raw) - allowed
    if extra:
        raise ValueError(f"Unexpected input fields: {', '.join(sorted(extra))}")
    topics, questions = load_bank()
    profile = load_profile()
    entries = load_log()
    session_id = raw.get("session_id")
    tid, qid = raw.get("topic_id"), raw.get("question_id")
    status = raw.get("status")
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id is required")
    custom = isinstance(tid, str) and tid.startswith("custom:")
    if custom:
        if not isinstance(qid, str) or not qid.startswith(tid + ":"):
            raise ValueError("Custom question_id must belong to its topic")
        if not isinstance(raw.get("question_text"), str) or not raw["question_text"].strip():
            raise ValueError("Custom questions need question_text")
        points = raw.get("ideal_points")
        if not isinstance(points, list) or not 2 <= len(points) <= 8 or not all(
                isinstance(point, str) and point.strip() for point in points):
            raise ValueError("Custom questions need 2-8 ideal_points")
        if raw.get("category") not in ("technical", "situational", "behavioral"):
            raise ValueError("Custom questions need a valid category")
        previous = [e for e in entries if e.get("question_id") == qid]
        if previous and any(e.get("question_text") != raw["question_text"] for e in previous):
            raise ValueError("A custom question_id cannot change its question text")
    elif tid not in topics or qid not in questions or questions[qid][0] != tid:
        raise ValueError("question_id must belong to topic_id")
    if profile.get("topics") and tid not in profile["topics"]:
        raise ValueError("Topic is outside profile.yaml topics")
    if status not in ("scored", "skipped", "abandoned"):
        raise ValueError("status must be scored, skipped, or abandoned")
    difficulty = raw.get("difficulty", "medium" if custom else topics[tid]["difficulty"])
    if difficulty not in DIFFICULTIES:
        raise ValueError("Invalid difficulty")
    if type(raw.get("hint_used", False)) is not bool:
        raise ValueError("hint_used must be boolean")
    summary = raw.get("feedback_summary", "")
    if not isinstance(summary, str) or len(summary) > 500:
        raise ValueError("feedback_summary must be text of at most 500 characters")
    correction = raw.get("corrects")
    if correction and not any(e.get("timestamp") == correction for e in entries):
        raise ValueError("corrects must reference an existing timestamp")
    scores = raw.get("scores")
    if status == "scored":
        if not isinstance(scores, dict):
            raise ValueError("A scored attempt needs five dimension scores")
        score = overall(scores)
    elif scores is not None:
        raise ValueError("Skipped and abandoned attempts cannot have scores")
    else:
        score = None
    if "answer" in raw and not isinstance(raw["answer"], str):
        raise ValueError("answer must be text")
    attempt = 1 + sum(e.get("session_id") == session_id and e.get("question_id") == qid
                      for e in entries)
    now = datetime.now(IST).isoformat(timespec="microseconds")
    entry = {"timestamp": now, "session_id": session_id, "topic_id": tid, "question_id": qid,
             "difficulty": difficulty, "attempt": attempt, "scores": scores if status == "scored" else None,
             "overall": score, "hint_used": raw.get("hint_used", False), "status": status,
             "feedback_summary": summary}
    if custom:
        entry.update({"question_text": raw["question_text"], "ideal_points": points,
                      "category": raw["category"]})
    if correction:
        entry["corrects"] = correction
    if profile["store_answers"] and "answer" in raw:
        entry["answer"] = raw["answer"]
    encoded = (json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    fd = os.open(ROOT / "progress_log.jsonl", os.O_WRONLY | os.O_APPEND)
    try:
        remaining = memoryview(encoded)
        while remaining:
            written = os.write(fd, remaining)
            if written == 0:
                raise OSError("Log write returned zero bytes")
            remaining = remaining[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    if load_log()[-1] != entry:
        raise RuntimeError("Log write could not be verified")
    return entry


def select_question(session_id: str, topic_id: str | None, difficulty: str) -> dict:
    topics, questions = load_bank()
    profile, entries = load_profile(), load_log()
    topic_order = list(profile.get("topics") or topics)
    if any(tid not in topics for tid in topic_order):
        raise ValueError("profile.yaml contains an unknown topic id")
    allowed = set(topic_order)
    if topic_id:
        if topic_id not in topics or topic_id not in allowed:
            raise ValueError("Requested topic is unavailable for this profile")
        allowed = {topic_id}
    corrected = {e.get("corrects") for e in entries if e.get("corrects")}
    recent_session = [e for e in entries if e.get("session_id") == session_id and e.get("status") == "scored"
                      and e.get("timestamp") not in corrected]
    if difficulty == "adaptive":
        target = recent_session[-1].get("difficulty", "medium") if recent_session else "medium"
        if target not in DIFFICULTIES:
            target = "medium"
        if len(recent_session) >= 2:
            last_two = [e.get("overall") for e in recent_session[-2:]]
            index = DIFFICULTIES.index(target)
            if all(isinstance(x, (int, float)) and x >= 4.0 for x in last_two):
                target = DIFFICULTIES[min(index + 1, 2)]
            elif all(isinstance(x, (int, float)) and x < 2.5 for x in last_two):
                target = DIFFICULTIES[max(index - 1, 0)]
    else:
        if difficulty not in DIFFICULTIES:
            raise ValueError("Difficulty must be easy, medium, hard, or adaptive")
        target = difficulty
    cutoff = datetime.now(IST) - timedelta(days=7)
    used_in_session = {e.get("question_id") for e in entries if e.get("session_id") == session_id}
    recent_ids = set()
    for e in entries:
        try:
            if datetime.fromisoformat(e["timestamp"]) >= cutoff:
                recent_ids.add(e.get("question_id"))
        except (KeyError, TypeError, ValueError):
            continue
    candidates = []
    for qid, (tid, question) in questions.items():
        if tid not in allowed or qid in used_in_session or qid in recent_ids:
            continue
        history = [e for e in entries if e.get("topic_id") == tid and e.get("status") == "scored"
                   and e.get("timestamp") not in corrected
                   and isinstance(e.get("overall"), (int, float))]
        avg = sum(e["overall"] for e in history[-5:]) / len(history[-5:]) if history else 0.0
        last = max((e.get("timestamp", "") for e in entries if e.get("topic_id") == tid), default="")
        distance = abs(DIFFICULTIES.index(topics[tid]["difficulty"]) - DIFFICULTIES.index(target))
        candidates.append((distance, avg, last, topic_order.index(tid), qid, tid, question))
    if not candidates:
        return {"status": "no_eligible_question", "reason": "All matching questions were used this session or in the last 7 days. Choose another topic or request a retry."}
    distance, _, _, _, qid, tid, question = min(candidates, key=lambda item: item[:5])
    return {"status": "selected", "topic_id": tid, "question_id": qid,
            "difficulty": topics[tid]["difficulty"], "adaptive_target": target,
            "difficulty_distance": distance, "category": topics[tid].get("category"),
            "text": question["text"], "ideal_points": question["ideal_points"]}


def progress() -> dict:
    topics, _ = load_bank()
    entries = load_log()
    corrected = {e.get("corrects") for e in entries if e.get("corrects")}
    entries = [e for e in entries if e.get("timestamp") not in corrected]
    scored = [e for e in entries if e.get("status") == "scored" and isinstance(e.get("overall"), (int, float))]
    custom_topic_ids = sorted({e.get("topic_id") for e in entries
                               if isinstance(e.get("topic_id"), str) and e["topic_id"].startswith("custom:")})
    if not scored:
        by_topic = {tid: {"attempts": 0, "average": None, "trend": "Too few data points"} for tid in topics}
        by_topic.update({tid: {"attempts": 0, "average": None, "trend": "Too few data points"}
                         for tid in custom_topic_ids})
        return {"scored_attempts": 0, "questions_practiced": 0, "sessions": 0,
                "overall_average": None, "trend": "Need 10 completed sessions for a five-versus-five trend.",
                "topics": by_topic,
                "dimension_averages": {}, "strongest_dimension": None, "weakest_dimension": None,
                "streak_days": 0, "recommended_focus": "Complete a first practice question."}
    def avg(values):
        return round(sum(values) / len(values), 2) if values else None
    by_topic = {}
    for tid in topics:
        values = [e["overall"] for e in scored if e.get("topic_id") == tid]
        by_topic[tid] = {"attempts": len(values), "average": avg(values),
                         "trend": "Too few data points" if len(values) < 3 else "Enough for a basic comparison"}
    for tid in custom_topic_ids:
        values = [e["overall"] for e in scored if e.get("topic_id") == tid]
        by_topic[tid] = {"attempts": len(values), "average": avg(values),
                         "trend": "Too few data points" if len(values) < 3 else "Enough for a basic comparison"}
    dimension_averages = {key: avg([e["scores"][key] for e in scored if isinstance(e.get("scores"), dict) and key in e["scores"]])
                          for key in DIMENSIONS}
    observed = {k: v for k, v in dimension_averages.items() if v is not None}
    sessions = defaultdict(list)
    for e in scored:
        sessions[e["session_id"]].append(e)
    ordered = sorted(sessions.items(), key=lambda pair: max(x.get("timestamp", "") for x in pair[1]))
    session_averages = [avg([e["overall"] for e in group]) for _, group in ordered]
    trend = ({"last_5_sessions": avg(session_averages[-5:]), "previous_5_sessions": avg(session_averages[-10:-5]),
              "change": round(avg(session_averages[-5:]) - avg(session_averages[-10:-5]), 2)}
             if len(session_averages) >= 10 else "Need 10 completed sessions for a five-versus-five trend.")
    dates = set()
    for e in scored:
        try:
            dates.add(datetime.fromisoformat(e["timestamp"]).astimezone(IST).date())
        except (KeyError, TypeError, ValueError):
            pass
    today = datetime.now(IST).date()
    day = today if today in dates else today - timedelta(days=1)
    streak = 0
    while day in dates:
        streak += 1
        day -= timedelta(days=1)
    weak_topic = min((tid for tid in topics if by_topic[tid]["attempts"] >= 3),
                     key=lambda tid: by_topic[tid]["average"], default=None)
    focus = (f"Practice one {weak_topic} question and target the weakest rubric dimension."
             if weak_topic else "Practice each topic at least three times before drawing a topic trend.")
    return {"scored_attempts": len(scored),
            "questions_practiced": len({(e["session_id"], e["question_id"]) for e in scored}),
            "sessions": len(sessions), "overall_average": avg([e["overall"] for e in scored]),
            "trend": trend, "topics": by_topic, "dimension_averages": dimension_averages,
            "strongest_dimension": max(observed, key=observed.get),
            "weakest_dimension": min(observed, key=observed.get),
            "streak_days": streak, "recommended_focus": focus}


def session_summary(session_id: str) -> dict:
    entries = load_log()
    corrected = {e.get("corrects") for e in entries if e.get("corrects")}
    session_entries = [e for e in entries if e.get("session_id") == session_id
                       and e.get("timestamp") not in corrected]
    scored = [e for e in session_entries if e.get("status") == "scored"
              and isinstance(e.get("overall"), (int, float))]
    if not session_entries:
        return {"session_id": session_id, "status": "not_found"}
    averages = {key: round(sum(e["scores"][key] for e in scored) / len(scored), 2)
                for key in DIMENSIONS} if scored else {}
    weakest = min(averages, key=averages.get) if averages else None
    strongest = max(averages, key=averages.get) if averages else None
    topic_map, question_map = load_bank()
    question_reviews = []
    groups = {"correct": [], "partly_correct": [], "incorrect": [], "not_assessed": [],
              "strong": [], "developing": [], "needs_work": []}
    for entry in session_entries:
        question = question_map.get(entry.get("question_id"))
        category = topic_map[question[0]].get("category") if question else entry.get("category")
        review = {"topic_id": entry.get("topic_id"), "question_id": entry.get("question_id"),
                  "attempt": entry.get("attempt"), "status": entry.get("status"),
                  "feedback_summary": entry.get("feedback_summary", ""),
                  "question": question[1]["text"] if question else entry.get("question_text"),
                  "category": category}
        if entry.get("status") == "scored" and isinstance(entry.get("scores"), dict):
            lowest = min(entry["scores"].values())
            relevance = entry["scores"]["relevance"]
            assessment = ("correct" if relevance >= 4 else
                          "partly_correct" if relevance == 3 else "incorrect")
            if category == "behavioral":
                assessment = {"correct": "strong", "partly_correct": "developing",
                              "incorrect": "needs_work"}[assessment]
            review.update({"overall": entry.get("overall"), "band": band(entry["overall"]),
                           "scores": entry["scores"], "assessment": assessment,
                           "lowest_dimensions": [key for key in DIMENSIONS if entry["scores"][key] == lowest]})
            groups[assessment].append(review)
        else:
            groups["not_assessed"].append(review)
        question_reviews.append(review)
    return {"session_id": session_id, "scored_questions": len({e["question_id"] for e in scored}),
            "scored_attempts": len(scored),
            "skipped": sum(e.get("status") == "skipped" for e in session_entries),
            "abandoned": sum(e.get("status") == "abandoned" for e in session_entries),
            "average_score": round(sum(e["overall"] for e in scored) / len(scored), 2) if scored else None,
            "dimension_averages": averages,
            "question_reviews": question_reviews,
            "correct_questions": groups["correct"],
            "partly_correct_questions": groups["partly_correct"],
            "incorrect_questions": groups["incorrect"],
            "behavioral_reviews": groups["strong"] + groups["developing"] + groups["needs_work"],
            "other_questions": groups["not_assessed"],
            "demonstrated_strengths": [strongest] if strongest and averages[strongest] >= 4 else [],
            "weak_points": [key for key, value in averages.items() if value <= 3],
            "strongest_dimension": strongest,
            "weakest_dimension": weakest,
            "recommended_focus": (f"Practice the {weakest} dimension on one new question."
                                  if weakest else "Complete a scored question before drawing a focus.")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create private profile and empty log from public defaults")
    p = sub.add_parser("record", help="Append and verify one attempt from a JSON input file")
    p.add_argument("--input", type=Path, required=True)
    p = sub.add_parser("select", help="Select one eligible question")
    p.add_argument("--session-id", required=True)
    p.add_argument("--topic")
    p.add_argument("--difficulty", default="adaptive")
    p = sub.add_parser("score", help="Calculate the fixed weighted rubric score")
    p.add_argument("--scores", required=True, help="Five whole numbers: relevance,structure,depth,communication,impact")
    sub.add_parser("progress", help="Compute progress from the append-only log")
    sub.add_parser("topics", help="Show topic counts and averages")
    p = sub.add_parser("session", help="Summarize one practice session")
    p.add_argument("--session-id", required=True)
    p = sub.add_parser("export", help="Export the full log")
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("delete", help="Delete all log entries after user confirmation")
    p.add_argument("--confirm", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = initialize()
        elif args.command == "record":
            result = record(args.input)
        elif args.command == "select":
            result = select_question(args.session_id, args.topic, args.difficulty)
        elif args.command == "progress":
            result = progress()
        elif args.command == "score":
            values = [int(part.strip()) for part in args.scores.split(",")]
            if len(values) != len(DIMENSIONS):
                raise ValueError("Supply five comma-separated dimension scores")
            scores = dict(zip(DIMENSIONS, values))
            value = overall(scores)
            result = {"scores": scores, "overall": value, "band": band(value)}
        elif args.command == "topics":
            result = progress()["topics"]
        elif args.command == "session":
            result = session_summary(args.session_id)
        elif args.command == "export":
            load_log()
            shutil.copyfile(ROOT / "progress_log.jsonl", args.output)
            result = {"exported": str(args.output), "entries": len(load_log())}
        else:
            if args.confirm != "YES":
                raise ValueError("Deletion requires explicit confirmation: --confirm YES")
            entries = load_log()
            temp = ROOT / "progress_log.jsonl.empty"
            temp.write_text("", encoding="utf-8")
            os.replace(temp, ROOT / "progress_log.jsonl")
            result = {"deleted_entries": len(entries), "remaining_entries": len(load_log())}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()

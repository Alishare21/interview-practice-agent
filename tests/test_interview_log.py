import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src import interview_log as app


TOPICS = """topics:
  - id: software-debugging
    category: technical
    difficulty: easy
    questions:
      - id: sd-001
        text: Debug an empty list.
        ideal_points: [reproduce, test]
  - id: sql-analytics
    category: technical
    difficulty: medium
    questions:
      - id: sql-001
        text: Explain GROUP BY.
        ideal_points: [group, aggregate]
  - id: statistics-reasoning
    category: technical
    difficulty: hard
    questions:
      - id: sr-001
        text: Explain A/B testing.
        ideal_points: [randomize, uncertainty]
"""


class InterviewLogTests(unittest.TestCase):
    def setUp(self):
        test_temp = Path(__file__).parent / ".tmp"
        test_temp.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=test_temp)
        self.root = Path(self.temp.name)
        (self.root / "topics.yaml").write_text(TOPICS, encoding="utf-8")
        (self.root / "profile.yaml").write_text("target_role: general software/data interviews\ntopics: []\nstore_answers: false\n", encoding="utf-8")
        (self.root / "progress_log.jsonl").write_text("", encoding="utf-8")
        self.root_patch = patch.object(app, "ROOT", self.root)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.temp.cleanup()

    def write_input(self, data):
        path = self.root / "input.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def scored_input(self, scores, question="sql-001", topic="sql-analytics", **extra):
        return {"session_id": "session-1", "topic_id": topic, "question_id": question,
                "status": "scored", "scores": scores, "hint_used": False,
                "feedback_summary": "A concise and specific review.", **extra}

    def test_weighted_example_uses_specified_boundary(self):
        scores = {"relevance": 4, "structure": 4, "depth": 3, "communication": 4, "impact": 3}
        self.assertEqual(app.overall(scores), 3.6)
        self.assertEqual(app.band(3.6), "Strong")
        with self.assertRaises(ValueError):
            app.overall({**scores, "impact": 0})

    def test_record_appends_without_private_answer_and_correction_supersedes_progress(self):
        scores = {key: 4 for key in app.DIMENSIONS}
        first = app.record(self.write_input(self.scored_input(scores, answer="private answer")))
        self.assertEqual(first["attempt"], 1)
        self.assertNotIn("answer", first)
        self.assertEqual(first["overall"], 4.0)
        second = app.record(self.write_input(self.scored_input(
            {key: 5 for key in app.DIMENSIONS}, corrects=first["timestamp"])))
        self.assertEqual(second["attempt"], 2)
        lines = (self.root / "progress_log.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0]), first)
        self.assertEqual(app.progress()["overall_average"], 5.0)
        self.assertEqual(app.progress()["questions_practiced"], 1)
        self.assertEqual(app.session_summary("session-1")["average_score"], 5.0)
        self.assertEqual(app.session_summary("session-1")["scored_questions"], 1)
        self.assertEqual(app.session_summary("session-1")["question_reviews"][0]["feedback_summary"],
                         "A concise and specific review.")

    def test_skip_has_no_score_and_recent_question_is_excluded(self):
        skipped = app.record(self.write_input({"session_id": "session-1", "topic_id": "sql-analytics",
                                               "question_id": "sql-001", "status": "skipped",
                                               "hint_used": True, "feedback_summary": "Skipped."}))
        self.assertIsNone(skipped["overall"])
        self.assertEqual(app.progress()["scored_attempts"], 0)
        selected = app.select_question("session-2", None, "medium")
        self.assertNotEqual(selected["question_id"], "sql-001")

    def test_adaptive_moves_up_after_two_strong_answers(self):
        for qid, tid in (("sd-001", "software-debugging"), ("sql-001", "sql-analytics")):
            app.record(self.write_input(self.scored_input(
                {key: 5 for key in app.DIMENSIONS}, question=qid, topic=tid,
                difficulty="medium")))
        selected = app.select_question("session-1", None, "adaptive")
        self.assertEqual(selected["adaptive_target"], "hard")
        self.assertEqual(selected["question_id"], "sr-001")

    def test_export_and_delete_require_explicit_yes(self):
        app.record(self.write_input(self.scored_input({key: 3 for key in app.DIMENSIONS})))
        export = self.root / "export.jsonl"
        with patch.object(sys, "argv", ["interview_log.py", "export", "--output", str(export)]):
            app.main()
        self.assertEqual(export.read_bytes(), (self.root / "progress_log.jsonl").read_bytes())
        with patch.object(sys, "argv", ["interview_log.py", "delete", "--confirm", "NO"]):
            with self.assertRaises(SystemExit):
                app.main()
        self.assertEqual(len(app.load_log()), 1)
        with patch.object(sys, "argv", ["interview_log.py", "delete", "--confirm", "YES"]):
            app.main()
        self.assertEqual(app.load_log(), [])

    def test_fresh_clone_runs_question_to_progress_without_storing_answer(self):
        (self.root / "profile.example.yaml").write_text(
            "target_role: general software/data interviews\ntopics: []\nstore_answers: false\n",
            encoding="utf-8")
        (self.root / "rubric.md").write_text("Fixed five-dimension rubric.\n", encoding="utf-8")
        (self.root / "profile.yaml").unlink()
        (self.root / "progress_log.jsonl").unlink()
        self.assertEqual(len(app.initialize()["created"]), 2)
        self.assertEqual(app.initialize()["created"], [])
        selected = app.select_question("fresh-session", "sql-analytics", "medium")
        self.assertEqual(selected["question_id"], "sql-001")
        entry = app.record(self.write_input({
            "session_id": "fresh-session", "topic_id": selected["topic_id"],
            "question_id": selected["question_id"], "difficulty": selected["difficulty"],
            "status": "scored", "scores": {key: 4 for key in app.DIMENSIONS},
            "feedback_summary": "Correct grouping with a small clarity gap.",
            "answer": "A fictional candidate answer."}))
        self.assertEqual(entry["overall"], 4.0)
        self.assertNotIn("answer", entry)
        self.assertEqual(app.session_summary("fresh-session")["average_score"], 4.0)
        self.assertEqual(app.session_summary("fresh-session")["question_reviews"][0]["lowest_dimensions"],
                         list(app.DIMENSIONS))
        self.assertEqual(app.progress()["questions_practiced"], 1)

    def test_session_review_exposes_wrong_step_and_weak_dimensions(self):
        summary = "Returned sorted positions, not original indices; keep original indices in the lookup."
        entry = app.record(self.write_input(self.scored_input(
            {"relevance": 1, "structure": 2, "depth": 1, "communication": 3, "impact": 1},
            question="sd-001", topic="software-debugging", feedback_summary=summary)))
        self.assertEqual(entry["overall"], 1.4)
        review = app.session_summary("session-1")["question_reviews"][0]
        self.assertEqual(review["feedback_summary"], summary)
        self.assertEqual(review["lowest_dimensions"], ["relevance", "depth", "impact"])

    def test_end_report_groups_answers_and_identifies_evidenced_areas(self):
        app.record(self.write_input(self.scored_input(
            {"relevance": 5, "structure": 5, "depth": 5, "communication": 5, "impact": 5},
            question="sql-001", topic="sql-analytics")))
        app.record(self.write_input(self.scored_input(
            {"relevance": 1, "structure": 2, "depth": 1, "communication": 2, "impact": 1},
            question="sd-001", topic="software-debugging",
            feedback_summary="Missed the empty-list case and a regression test.")))
        report = app.session_summary("session-1")
        self.assertEqual([item["question_id"] for item in report["correct_questions"]], ["sql-001"])
        self.assertEqual([item["question_id"] for item in report["incorrect_questions"]], ["sd-001"])
        self.assertEqual(report["incorrect_questions"][0]["question"], "Debug an empty list.")
        self.assertIn("depth", report["weak_points"])


if __name__ == "__main__":
    unittest.main()

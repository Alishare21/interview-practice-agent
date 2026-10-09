import unittest

from web_app import custom_question_id, ensure_session_scoped_question_id, planned_question_count


class SessionQuestionCountTests(unittest.TestCase):
    def test_user_selected_count_is_exact_for_custom_topics(self):
        self.assertEqual(planned_question_count(2, topic_count=4, starter_mode=False), 2)

    def test_default_custom_session_expands_for_topic_coverage(self):
        self.assertEqual(planned_question_count(10, topic_count=6, starter_mode=False), 12)

    def test_default_does_not_expand_below_ten(self):
        self.assertEqual(planned_question_count(10, topic_count=3, starter_mode=False), 10)

    def test_starter_bank_respects_the_selected_count(self):
        self.assertEqual(planned_question_count(2, topic_count=0, starter_mode=True), 2)

    def test_custom_question_ids_are_unique_across_sessions(self):
        first = custom_question_id("custom:python", "2026-10-09-01", 1)
        second = custom_question_id("custom:python", "2026-10-09-02", 1)
        self.assertNotEqual(first, second)
        self.assertTrue(second.startswith("custom:python:"))

    def test_in_progress_legacy_question_id_is_upgraded_for_retry(self):
        session = {
            "session_id": "2026-10-09-02",
            "question_history": [],
            "current": {
                "topic_id": "custom:python",
                "question_id": "custom:python:1",
                "custom": True,
            },
        }
        question_id = ensure_session_scoped_question_id(session)
        self.assertEqual(question_id, "custom:python:2026-10-09-02:1")


if __name__ == "__main__":
    unittest.main()

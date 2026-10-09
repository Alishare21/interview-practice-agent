import unittest

from web_app import planned_question_count


class SessionQuestionCountTests(unittest.TestCase):
    def test_user_selected_count_is_exact_for_custom_topics(self):
        self.assertEqual(planned_question_count(2, topic_count=4, starter_mode=False), 2)

    def test_default_custom_session_expands_for_topic_coverage(self):
        self.assertEqual(planned_question_count(10, topic_count=6, starter_mode=False), 12)

    def test_default_does_not_expand_below_ten(self):
        self.assertEqual(planned_question_count(10, topic_count=3, starter_mode=False), 10)

    def test_starter_bank_respects_the_selected_count(self):
        self.assertEqual(planned_question_count(2, topic_count=0, starter_mode=True), 2)


if __name__ == "__main__":
    unittest.main()

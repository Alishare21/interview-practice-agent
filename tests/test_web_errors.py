import unittest

from web_app import friendly_error


class WebErrorTests(unittest.TestCase):
    def test_credit_exhaustion_gets_clear_billing_guidance(self):
        message = friendly_error(RuntimeError(
            "Error code: 429 credit_balance_exhausted; You have no credits remaining."))
        self.assertIn("no credits remaining", message)
        self.assertIn("API billing settings", message)
        self.assertNotIn("credit_balance_exhausted", message)

    def test_unknown_provider_error_does_not_leak_raw_details(self):
        message = friendly_error(RuntimeError("secret response payload"))
        self.assertIn("couldn't complete that step", message)
        self.assertNotIn("secret response payload", message)

    def test_invalid_provider_key_has_actionable_message(self):
        class UnauthorizedError(Exception):
            status_code = 401

        message = friendly_error(UnauthorizedError("secret response payload"))
        self.assertIn("rejected its API key", message)
        self.assertNotIn("secret response payload", message)

    def test_bad_provider_request_exposes_status_without_raw_body(self):
        class BadRequestError(Exception):
            status_code = 400

        message = friendly_error(BadRequestError("private request details"))
        self.assertIn("HTTP 400", message)
        self.assertNotIn("private request details", message)

    def test_custom_question_collision_has_recovery_guidance(self):
        message = friendly_error(ValueError("A custom question_id cannot change its question text"))
        self.assertIn("wasn’t recorded", message)
        self.assertIn("Retry the answer", message)


if __name__ == "__main__":
    unittest.main()

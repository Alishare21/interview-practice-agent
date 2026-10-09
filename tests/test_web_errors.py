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


if __name__ == "__main__":
    unittest.main()

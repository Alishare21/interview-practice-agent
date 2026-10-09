import unittest
from unittest.mock import patch

import web_app


class AIProviderTests(unittest.TestCase):
    def test_groq_is_selected_and_uses_openai_compatible_endpoint(self):
        def fake_secret(name):
            return {"GROQ_API_KEY": "groq-test-key"}.get(name)

        with patch.object(web_app, "secret", side_effect=fake_secret):
            client, model, provider = web_app.ai_client()

        self.assertEqual(provider, "Groq")
        self.assertEqual(model, "openai/gpt-oss-20b")
        self.assertEqual(str(client.base_url).rstrip("/"), "https://api.groq.com/openai/v1")

    def test_openai_remains_available_as_fallback(self):
        def fake_secret(name):
            return {"OPENAI_API_KEY": "openai-test-key"}.get(name)

        with patch.object(web_app, "secret", side_effect=fake_secret):
            client, model, provider = web_app.ai_client()

        self.assertEqual(provider, "OpenAI")
        self.assertEqual(model, "gpt-4.1-mini")
        self.assertEqual(client.api_key, "openai-test-key")

    def test_no_key_returns_no_provider(self):
        with patch.object(web_app, "secret", return_value=None):
            self.assertIsNone(web_app.ai_client())


if __name__ == "__main__":
    unittest.main()

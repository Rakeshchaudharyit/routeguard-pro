"""Environment configuration regression tests; no network access required."""
from unittest import TestCase
from unittest.mock import patch
from .env import boolean_env, list_env, deployment_secret


class DeploymentEnvironmentTests(TestCase):
    def test_boolean_values(self):
        for value in ('true', '1', 'YES', 'on'):
            with self.subTest(value=value), patch.dict('os.environ', {'TEST_FLAG': value}):
                self.assertTrue(boolean_env('TEST_FLAG'))
        for value in ('false', '0', 'no', 'OFF'):
            with self.subTest(value=value), patch.dict('os.environ', {'TEST_FLAG': value}):
                self.assertFalse(boolean_env('TEST_FLAG', True))

    def test_invalid_boolean_fails_closed(self):
        with patch.dict('os.environ', {'TEST_FLAG': 'maybe'}):
            with self.assertRaises(ValueError):
                boolean_env('TEST_FLAG')

    def test_lists_strip_empty_items(self):
        with patch.dict('os.environ', {'TEST_LIST': ' example.com, ,api.example.com '}):
            self.assertEqual(list_env('TEST_LIST'), ['example.com', 'api.example.com'])

    def test_production_secret_required(self):
        with patch.dict('os.environ', {'DJANGO_SECRET_KEY': 'short'}):
            with self.assertRaises(ValueError):
                deployment_secret(False)

    def test_valid_production_secret(self):
        secret = 'a-unique-random-secret-' + 'x' * 50
        with patch.dict('os.environ', {'DJANGO_SECRET_KEY': secret}):
            self.assertEqual(deployment_secret(False), secret)

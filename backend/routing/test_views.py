from django.test import SimpleTestCase, Client
from rest_framework.test import APIClient

class HealthEndpointTests(SimpleTestCase):
    def test_health_is_json_and_returns_200(self):
        response = APIClient().get('/api/health/', HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['status'], 'ok')

    def test_health_ignores_browser_accept_header(self):
        for accept in ('text/html', 'application/json', '*/*'):
            with self.subTest(accept=accept):
                response = Client().get('/api/health/', HTTP_ACCEPT=accept)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Content-Type'], 'application/json')
                self.assertEqual(response.json()['status'], 'ok')

    def test_health_rejects_post(self):
        response = Client().post('/api/health/')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response['Content-Type'], 'application/json')

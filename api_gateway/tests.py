from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from organizations.models import Organization
from api_gateway.models import APIClient, APIKey, RateLimitPolicy, APIGatewayRequestLog
from api_gateway.services import APIKeyManager, RateLimiterService

User = get_user_model()

class APIGatewayTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='api_admin', email='api@nexora.io', password='Password123!', role='SUPER_ADMIN')
        self.org = Organization.objects.create(name='Nexora Enterprise Cloud')
        self.policy = RateLimitPolicy.objects.create(name='Standard Developer Tier', requests_per_minute=100, is_default=True)
        self.client_app = APIClient.objects.create(
            client_name='Acme Logistics Integration App',
            organization=self.org,
            contact_email='dev@acmelogistics.com',
            rate_limit_policy=self.policy
        )
        self.key_obj, self.raw_key = APIKeyManager.generate_api_key(self.client_app, name='Acme Production Key')

        self.client = Client()
        self.client.force_login(self.user)

    def test_key_verification_and_revocation(self):
        # Verify valid key
        verified = APIKeyManager.verify_key(self.raw_key)
        self.assertIsNotNone(verified)
        self.assertEqual(verified.client.client_name, 'Acme Logistics Integration App')
        self.assertEqual(verified.total_calls_count, 1)

        # Revoke key
        APIKeyManager.revoke_key(self.key_obj.id)
        verified_after = APIKeyManager.verify_key(self.raw_key)
        self.assertIsNone(verified_after)

    def test_gateway_ping_endpoint(self):
        res = self.client.get(reverse('api_gateway:api_ping'), HTTP_X_NEXORA_API_KEY=self.raw_key)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'ok')
        self.assertTrue(data['authenticated'])

    def test_views(self):
        res_dash = self.client.get(reverse('api_gateway:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_clients = self.client.get(reverse('api_gateway:client_list'))
        self.assertEqual(res_clients.status_code, 200)

        res_logs = self.client.get(reverse('api_gateway:log_list'))
        self.assertEqual(res_logs.status_code, 200)
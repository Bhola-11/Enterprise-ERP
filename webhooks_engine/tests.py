from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from webhooks_engine.models import WebhookEndpoint, WebhookEvent, WebhookDeliveryAttempt
from webhooks_engine.services import HMACSignatureEngine, WebhookDispatcher

User = get_user_model()

class WebhooksEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='wh_admin', email='wh@nexora.io', password='Password123!', role='SUPER_ADMIN')
        self.secret = 'test_secret_key_8928374982374'
        self.endpoint = WebhookEndpoint.objects.create(
            name='Shopify ERP Sync Hook',
            target_url='https://shopify.nexora-store.com/webhooks',
            secret_key=self.secret,
            subscribed_events=['sales.order.created', 'inventory.stock.low'],
            is_active=True
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_hmac_signature_calculation_and_verification(self):
        payload = {'order_id': 101, 'status': 'PAID', 'amount': '150.00'}
        sig = HMACSignatureEngine.compute_signature(payload, self.secret)
        self.assertTrue(sig.startswith('sha256='))
        self.assertTrue(HMACSignatureEngine.verify_signature(payload, sig, self.secret))

    def test_webhook_dispatch_flow(self):
        event, attempts = WebhookDispatcher.trigger_event(
            topic='sales.order.created',
            payload_data={'order_number': 'SO-9900', 'total': '500.00'}
        )
        self.assertEqual(len(attempts), 1)
        attempt = attempts[0]
        self.assertEqual(attempt.status, 'DELIVERED')
        self.assertEqual(attempt.http_status_code, 200)

        self.endpoint.refresh_from_db()
        self.assertEqual(self.endpoint.total_deliveries_count, 1)

    def test_views(self):
        res_dash = self.client.get(reverse('webhooks_engine:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_endpoints = self.client.get(reverse('webhooks_engine:endpoint_list'))
        self.assertEqual(res_endpoints.status_code, 200)

        res_deliveries = self.client.get(reverse('webhooks_engine:delivery_list'))
        self.assertEqual(res_deliveries.status_code, 200)
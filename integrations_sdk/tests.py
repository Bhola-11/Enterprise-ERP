from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from sales.models import Customer
from integrations_sdk.models import IntegrationConnector, EntitySyncMapping, IntegrationSyncLog
from integrations_sdk.services import IntegrationSyncRunner

User = get_user_model()

class IntegrationsSDKTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='integration_admin', email='sdk@nexora.io', password='Password123!', role='SUPER_ADMIN')
        self.customer = Customer.objects.create(
            first_name='Lockheed',
            last_name='Martin',
            company_name='Lockheed Martin Aeronautics',
            email='procurement@lockheed.com',
            billing_address='100 Aerospace Blvd',
            city='Bethesda'
        )
        self.connector = IntegrationConnector.objects.create(
            name='Stripe Primary Gateway',
            connector_type='STRIPE',
            auth_type='API_KEY',
            is_active=True
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_sync_execution_and_mapping(self):
        log = IntegrationSyncRunner.execute_sync(self.connector, sync_type='TEST_RUN')
        self.assertEqual(log.status, 'SUCCESS')
        self.assertTrue(log.records_processed > 0)

        # Check mapping created
        mapping = EntitySyncMapping.objects.filter(connector=self.connector, local_id=self.customer.id).first()
        self.assertIsNotNone(mapping)
        self.assertTrue(mapping.external_reference_id.startswith('cus_stripe_'))

    def test_views(self):
        res_market = self.client.get(reverse('integrations_sdk:marketplace'))
        self.assertEqual(res_market.status_code, 200)

        res_conn = self.client.get(reverse('integrations_sdk:connector_detail', args=[self.connector.id]))
        self.assertEqual(res_conn.status_code, 200)

        res_logs = self.client.get(reverse('integrations_sdk:sync_log_list'))
        self.assertEqual(res_logs.status_code, 200)
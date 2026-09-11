from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from organizations.models import Organization
from accounting.models import Account
from consolidation.models import ConsolidationGroup, CurrencyExchangeRate, InterCompanyEliminationRule, ConsolidatedStatement
from consolidation.services import ConsolidationEngine, IAS21CurrencyTranslator

User = get_user_model()

class ConsolidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cons_cfo', email='cfo@nexora.io', password='Password123!', role='SUPER_ADMIN')
        self.parent_org = Organization.objects.create(name='Nexora Global Holdings Inc.', currency='USD')
        self.sub_org = Organization.objects.create(name='Nexora Europe GmbH', currency='EUR')

        self.account = Account.objects.create(
            code='1100', name='Trade Accounts Receivable', account_type='ASSET',
            balance=Decimal('100000.00'), is_active=True
        )

        self.group = ConsolidationGroup.objects.create(
            name='Nexora Worldwide Group', code='GRP-NEXORA-WW',
            parent_organization=self.parent_org, reporting_currency='USD'
        )
        self.group.subsidiary_organizations.add(self.sub_org)

        self.rate = CurrencyExchangeRate.objects.create(
            from_currency='EUR', to_currency='USD',
            spot_rate=Decimal('1.085000'), average_monthly_rate=Decimal('1.080000'), closing_rate=Decimal('1.090000')
        )

        self.rule = InterCompanyEliminationRule.objects.create(
            group=self.group, rule_name='Eliminate Intercompany AR/AP',
            rule_type='AR_AP_BALANCE', source_account_code='1100', offset_account_code='2010'
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_consolidation_calculation_and_elimination(self):
        stmt = ConsolidationEngine.generate_consolidated_report(
            group=self.group,
            statement_type='BALANCE_SHEET',
            period_start='2026-01-01',
            period_end='2026-12-31',
            user=self.user
        )
        self.assertEqual(stmt.status, 'ELIMINATED')
        self.assertTrue(stmt.gross_total_parent > Decimal('0.00'))
        self.assertTrue(stmt.gross_total_subsidiaries > Decimal('0.00'))
        self.assertTrue(stmt.total_eliminations > Decimal('0.00'))
        self.assertEqual(stmt.net_consolidated_total, stmt.gross_total_parent + stmt.gross_total_subsidiaries - stmt.total_eliminations)

    def test_views(self):
        res_dash = self.client.get(reverse('consolidation:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_groups = self.client.get(reverse('consolidation:group_list'))
        self.assertEqual(res_groups.status_code, 200)

        res_rates = self.client.get(reverse('consolidation:rates_list'))
        self.assertEqual(res_rates.status_code, 200)

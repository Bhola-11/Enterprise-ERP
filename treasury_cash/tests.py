from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounting.models import Account, BankAccount
from treasury_cash.models import CashPoolHeader, CashPoolParticipant, CashSweepingExecution, LiquidityForecast, FXHedgingContract
from treasury_cash.services import CashSweepingEngine, LiquidityForecastingService

User = get_user_model()

class TreasuryCashTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='treasury_mgr', email='treasury@nexora.io', password='Password123!', role='SUPER_ADMIN')
        self.gl_acc1 = Account.objects.create(code='1010', name='Master Cash Account', account_type='ASSET', is_active=True)
        self.gl_acc2 = Account.objects.create(code='1020', name='Sub Cash Account', account_type='ASSET', is_active=True)

        self.leader_bank = BankAccount.objects.create(
            account_name='Master Concentration Account',
            bank_name='J.P. Morgan Global Master Treasury',
            account_number='JPM-9928172',
            gl_account=self.gl_acc1,
            balance=Decimal('500000.00'),
            is_active=True
        )
        self.sub_bank = BankAccount.objects.create(
            account_name='Silicon Valley Operating Account',
            bank_name='Silicon Valley Bank',
            account_number='SVB-1029384',
            gl_account=self.gl_acc2,
            balance=Decimal('150000.00'),
            is_active=True
        )

        self.pool = CashPoolHeader.objects.create(
            name='North America Sweeping Pool',
            pool_code='POOL-NA-01',
            pool_method='TARGET_BALANCE_SWEEP',
            pool_leader_bank=self.leader_bank,
            target_balance_amount=Decimal('50000.00')
        )
        self.part = CashPoolParticipant.objects.create(
            pool=self.pool,
            bank_account=self.sub_bank,
            min_transfer_threshold=Decimal('5000.00')
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_cash_sweeping_execution(self):
        # Sub bank has 150,000, target is 50,000 -> 100,000 should be swept to leader
        execution = CashSweepingEngine.execute_sweeping_run(self.pool, user=self.user)
        self.assertEqual(execution.status, 'COMPLETED')
        self.assertEqual(execution.total_swept_in, Decimal('100000.00'))

        self.sub_bank.refresh_from_db()
        self.leader_bank.refresh_from_db()
        self.assertEqual(self.sub_bank.balance, Decimal('50000.00'))
        self.assertEqual(self.leader_bank.balance, Decimal('600000.00'))

    def test_liquidity_forecasting(self):
        forecast = LiquidityForecastingService.generate_90day_forecast()
        self.assertIsNotNone(forecast)
        self.assertTrue(forecast.projected_closing_balance > Decimal('0.00'))

    def test_views(self):
        res_dash = self.client.get(reverse('treasury_cash:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_pools = self.client.get(reverse('treasury_cash:pool_list'))
        self.assertEqual(res_pools.status_code, 200)

        res_hedging = self.client.get(reverse('treasury_cash:hedging_list'))
        self.assertEqual(res_hedging.status_code, 200)

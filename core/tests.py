from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from organizations.models import Organization, Branch, Department, FiscalYear
from accounts.models import User, UserProfile
from crm.models import Company, Contact, Lead, Opportunity
from inventory.models import ProductCategory, ProductBrand, UnitOfMeasure, Product, StockMovement
from inventory.services import StockService
from warehouse.models import Warehouse, Zone, Bin
from purchasing.models import Supplier, PurchaseOrder, PurchaseOrderItem
from sales.models import Customer, SalesOrder, SalesOrderItem, Invoice, InvoiceItem, Payment
from accounting.models import Account, JournalEntry, JournalItem
from accounting.services import AccountingService
from hr.models import Designation, Employee
from manufacturing.models import WorkCenter, BillOfMaterials, BOMItem, ProductionOrder

class EnterpriseOSCoreTestSuite(TestCase):
    def setUp(self):
        self.client = Client()

        # Organization & Hierarchy
        self.org = Organization.objects.create(name='Nexora Test Corp', tax_id='TAX-12345')
        self.branch = Branch.objects.create(organization=self.org, name='Test HQ', code='THQ', city='New York')
        self.dept = Department.objects.create(organization=self.org, branch=self.branch, name='Finance', code='FIN')
        self.fiscal_year = FiscalYear.objects.create(organization=self.org, title='FY 2026', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))

        # Admin & Staff Users
        self.admin_user = User.objects.create_superuser(
            email='admin@nexoratest.com',
            password='testpassword123',
            first_name='Alexander',
            last_name='Admin'
        )
        self.sales_user = User.objects.create_user(
            email='sales@nexoratest.com',
            password='testpassword123',
            first_name='Sarah',
            last_name='Sales',
            role='SALES_MANAGER'
        )
        self.finance_user = User.objects.create_user(
            email='finance@nexoratest.com',
            password='testpassword123',
            first_name='Frank',
            last_name='Finance',
            role='ACCOUNTANT'
        )

        # Chart of Accounts
        self.cash_acc = Account.objects.create(code='1010', name='Cash Account', account_type='ASSET', balance=Decimal('50000.00'))
        self.ar_acc = Account.objects.create(code='1050', name='Accounts Receivable', account_type='ASSET', balance=Decimal('0.00'))
        self.sales_rev_acc = Account.objects.create(code='4010', name='Sales Revenue', account_type='REVENUE', balance=Decimal('0.00'))
        self.cogs_acc = Account.objects.create(code='5010', name='COGS', account_type='EXPENSE', balance=Decimal('0.00'))

        # Inventory Setup
        self.uom = UnitOfMeasure.objects.create(name='Unit', symbol='EA')
        self.cat = ProductCategory.objects.create(name='Hardware', code='HW')
        self.product = Product.objects.create(
            name='Test Compute Node',
            sku='NODE-001',
            barcode='BARCODE-NODE-001',
            category=self.cat,
            uom=self.uom,
            cost_price=Decimal('100.00'),
            selling_price=Decimal('250.00'),
            current_stock=Decimal('50.00')
        )

    def test_authentication_and_dashboard_access(self):
        # Anonymous redirect to landing or login
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)

        # Login admin user
        login_success = self.client.login(username='admin@nexoratest.com', password='testpassword123')
        self.assertTrue(login_success)

        # Access dashboard
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Executive Operations Dashboard')

    def test_accounting_double_entry_journal_validation(self):
        # Create balanced journal entry
        je = JournalEntry.objects.create(
            entry_number='JE-TEST-001',
            date=date.today(),
            fiscal_year=self.fiscal_year,
            narration='Recognize customer sales',
            total_debit=Decimal('2500.00'),
            total_credit=Decimal('2500.00'),
            status='DRAFT',
            created_by=self.finance_user
        )
        JournalItem.objects.create(journal_entry=je, account=self.ar_acc, debit=Decimal('2500.00'), credit=Decimal('0.00'))
        JournalItem.objects.create(journal_entry=je, account=self.sales_rev_acc, debit=Decimal('0.00'), credit=Decimal('2500.00'))

        self.assertTrue(je.is_balanced)

        # Post journal entry via AccountingService
        AccountingService.post_journal_entry(je, self.finance_user)
        je.refresh_from_db()
        self.assertEqual(je.status, 'POSTED')

        # Verify Account Balances
        self.ar_acc.refresh_from_db()
        self.sales_rev_acc.refresh_from_db()
        self.assertEqual(self.ar_acc.balance, Decimal('2500.00'))
        self.assertEqual(self.sales_rev_acc.balance, Decimal('2500.00'))

    def test_inventory_stock_service_ledger(self):
        initial_stock = self.product.current_stock
        movement = StockService.record_movement(
            product=self.product,
            movement_type='PURCHASE_RECEIPT',
            quantity=Decimal('25.00'),
            unit_cost=Decimal('100.00'),
            reference_number='PO-TEST-001',
            user=self.admin_user,
            notes='Stock receipt test'
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, initial_stock + Decimal('25.00'))
        self.assertEqual(movement.balance_after, initial_stock + Decimal('25.00'))

    def test_crm_and_lead_conversion_workflow(self):
        lead = Lead.objects.create(
            first_name='John',
            last_name='Prospect',
            email='john@prospect.com',
            company_name='Prospect Enterprise',
            estimated_budget=Decimal('50000.00'),
            assigned_to=self.sales_user
        )

        self.client.login(username='sales@nexoratest.com', password='testpassword123')
        convert_url = reverse('crm:lead_convert', kwargs={'pk': lead.id})
        response = self.client.post(convert_url, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verify company and opportunity created
        lead.refresh_from_db()
        self.assertEqual(lead.status, 'CONVERTED')
        self.assertTrue(Company.objects.filter(name='Prospect Enterprise').exists())
        self.assertTrue(Opportunity.objects.filter(lead=lead).exists())

    def test_sales_cycle_order_to_payment(self):
        cust = Customer.objects.create(
            first_name='Alice',
            last_name='Client',
            company_name='Client Dynamics Inc',
            email='alice@client.com',
            phone='+1-555-9000',
            billing_address='100 Main St',
            city='Boston'
        )

        # Create Sales Order
        order = SalesOrder.objects.create(
            order_number='SO-TEST-100',
            customer=cust,
            order_date=date.today(),
            subtotal=Decimal('2500.00'),
            tax_amount=Decimal('250.00'),
            total_amount=Decimal('2750.00'),
            status='CONFIRMED',
            created_by=self.sales_user
        )
        SalesOrderItem.objects.create(order=order, product=self.product, quantity=Decimal('10.00'), unit_price=Decimal('250.00'), total=Decimal('2500.00'))

        # Create Invoice
        invoice = Invoice.objects.create(
            invoice_number='INV-TEST-100',
            sales_order=order,
            customer=cust,
            invoice_date=date.today(),
            due_date=date.today(),
            subtotal=Decimal('2500.00'),
            tax_amount=Decimal('250.00'),
            total_amount=Decimal('2750.00'),
            paid_amount=Decimal('0.00'),
            balance_due=Decimal('2750.00'),
            status='ISSUED',
            created_by=self.finance_user
        )

        # Record Payment
        Payment.objects.create(
            payment_number='PAY-TEST-100',
            invoice=invoice,
            customer=cust,
            amount=Decimal('2750.00'),
            payment_method='BANK_TRANSFER',
            payment_date=date.today(),
            created_by=self.finance_user
        )
        invoice.paid_amount = Decimal('2750.00')
        invoice.update_balance()

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'PAID')
        self.assertEqual(invoice.balance_due, Decimal('0.00'))

    def test_manufacturing_bom_calculation(self):
        raw_mat = Product.objects.create(
            name='Steel Plate',
            sku='RAW-STEEL',
            barcode='BARCODE-RAW-001',
            category=self.cat,
            uom=self.uom,
            cost_price=Decimal('20.00'),
            selling_price=Decimal('30.00'),
            current_stock=Decimal('200.00')
        )
        bom = BillOfMaterials.objects.create(
            bom_number='BOM-TEST-001',
            finished_product=self.product,
            quantity=Decimal('1.00')
        )
        BOMItem.objects.create(bom=bom, raw_material=raw_mat, quantity=Decimal('4.00'))

        self.assertEqual(bom.total_raw_material_cost, Decimal('80.00'))

    def test_rest_api_endpoints(self):
        self.client.login(username='admin@nexoratest.com', password='testpassword123')
        
        # Test Products API endpoint
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)

        # Test Customers API endpoint
        response = self.client.get('/api/customers/')
        self.assertEqual(response.status_code, 200)

        # Test Invoices API endpoint
        response = self.client.get('/api/invoices/')
        self.assertEqual(response.status_code, 200)

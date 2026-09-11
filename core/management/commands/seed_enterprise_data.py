import os
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from organizations.models import Organization, Branch, Department, CostCenter, FiscalYear, TaxSetting
from accounts.models import User, UserProfile
from crm.models import Company, Contact, Campaign, Lead, Opportunity
from inventory.models import ProductCategory, ProductBrand, UnitOfMeasure, Product, StockMovement
from warehouse.models import Warehouse, Zone, Bin
from purchasing.models import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, GoodsReceiptItem
from sales.models import Customer, Quotation, QuotationItem, SalesOrder, SalesOrderItem, Invoice, InvoiceItem, Payment
from accounting.models import Account, JournalEntry, JournalItem, BankAccount
from hr.models import Designation, Employee, Attendance, LeaveType, LeaveRequest
from payroll.models import SalaryStructure, Payrun, Payslip
from projects.models import Project, Milestone, Task, Timesheet
from support.models import TicketCategory, SupportTicket, TicketComment
from assets.models import AssetCategory, Asset, AssetMaintenanceLog
from fleet.models import Driver, Vehicle, FuelLog, TripRecord
from manufacturing.models import WorkCenter, BillOfMaterials, BOMItem, ProductionOrder
from documents.models import Folder, Document
from workflows.models import WorkflowDefinition, WorkflowStage
from core.models import SystemSetting, IntegrationConfig
from notifications.models import Notification
from pos.models import POSTerminal, POSSession, POSCustomerLoyalty, POSCouponPromotion, POSOrder, POSOrderItem, POSPayment
from taxation.models import TaxJurisdiction, HSNSACCode, GSTTaxRate, EUVATRule, USStateNexusRate, EWayBillRecord, EInvoiceIRN
from reconciliation.models import BankStatement, BankStatementLine, ReconciliationRule

class Command(BaseCommand):
    help = 'Populates the ERP with realistic, interconnected enterprise demo data across all 24 modules'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting enterprise data seeding...'))

        # 1. Organization & Hierarchy
        org, _ = Organization.objects.get_or_create(
            name='Nexora Global Industries Inc.',
            defaults={
                'legal_name': 'Nexora Global Industries Incorporated',
                'tax_id': 'US-993847291-TX',
                'registration_number': 'DEL-CORP-2024-88392',
                'email': 'corporate@nexora.com',
                'phone': '+1 (800) 555-0199',
                'website': 'https://nexora.enterprise',
                'currency': 'USD',
                'currency_symbol': '$',
                'address': 'One World Trade Center, Suite 8500',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10007',
                'country': 'United States'
            }
        )
        self.stdout.write(f'Organization: {org.name}')

        # Branches
        branch_hq, _ = Branch.objects.get_or_create(
            organization=org, code='HQ-NYC',
            defaults={'name': 'Global HQ - New York', 'city': 'New York', 'country': 'USA', 'is_headquarters': True, 'address': 'One World Trade Center, Suite 8500'}
        )
        branch_emea, _ = Branch.objects.get_or_create(
            organization=org, code='EMEA-LON',
            defaults={'name': 'EMEA Operations Hub - London', 'city': 'London', 'country': 'UK', 'address': '10 Finsbury Square'}
        )
        branch_apac, _ = Branch.objects.get_or_create(
            organization=org, code='APAC-SIN',
            defaults={'name': 'APAC Tech Center - Singapore', 'city': 'Singapore', 'country': 'Singapore', 'address': '1 Marina Boulevard'}
        )

        # Departments
        dept_exec, _ = Department.objects.get_or_create(organization=org, code='EXEC', defaults={'name': 'Executive Board', 'branch': branch_hq})
        dept_sales, _ = Department.objects.get_or_create(organization=org, code='SALES', defaults={'name': 'Commercial & Global Sales', 'branch': branch_hq})
        dept_fin, _ = Department.objects.get_or_create(organization=org, code='FIN', defaults={'name': 'Corporate Finance & Accounting', 'branch': branch_hq})
        dept_scm, _ = Department.objects.get_or_create(organization=org, code='SCM', defaults={'name': 'Supply Chain & Warehousing', 'branch': branch_hq})
        dept_eng, _ = Department.objects.get_or_create(organization=org, code='ENG', defaults={'name': 'Product Engineering & R&D', 'branch': branch_apac})
        dept_hr, _ = Department.objects.get_or_create(organization=org, code='HR', defaults={'name': 'Human Capital Management', 'branch': branch_hq})
        dept_mfg, _ = Department.objects.get_or_create(organization=org, code='MFG', defaults={'name': 'Advanced Manufacturing', 'branch': branch_emea})
        dept_cs, _ = Department.objects.get_or_create(organization=org, code='CS', defaults={'name': 'Customer Success & Support', 'branch': branch_hq})

        # Cost Centers
        cc_ops, _ = CostCenter.objects.get_or_create(organization=org, code='CC-100', defaults={'name': 'Core Operations', 'department': dept_sales})
        cc_rd, _ = CostCenter.objects.get_or_create(organization=org, code='CC-200', defaults={'name': 'R&D Innovation', 'department': dept_eng})

        # Fiscal Year
        fy, _ = FiscalYear.objects.get_or_create(
            organization=org, title='FY 2026',
            defaults={'start_date': date(2026, 1, 1), 'end_date': date(2026, 12, 31), 'is_active': True}
        )

        # Taxes
        tax_standard, _ = TaxSetting.objects.get_or_create(organization=org, name='Standard Sales Tax', defaults={'rate': Decimal('8.50'), 'tax_code': 'SALES_TAX'})
        tax_vat, _ = TaxSetting.objects.get_or_create(organization=org, name='VAT European Standard', defaults={'rate': Decimal('20.00'), 'tax_code': 'VAT'})

        # 2. RBAC Users
        user_specs = [
            ('admin@nexora.com', 'admin12345', 'Alexander', 'Vance', 'SUPER_ADMIN', 'Executive Board', '+1-555-0101', 'Chief Executive Officer'),
            ('sales@nexora.com', 'admin12345', 'Elena', 'Rostova', 'SALES_MANAGER', 'Commercial & Global Sales', '+1-555-0102', 'VP of Sales'),
            ('finance@nexora.com', 'admin12345', 'Marcus', 'Sterling', 'ACCOUNTANT', 'Corporate Finance', '+1-555-0103', 'Principal Accountant'),
            ('inventory@nexora.com', 'admin12345', 'Devon', 'Miles', 'INVENTORY_MANAGER', 'Supply Chain', '+1-555-0104', 'Inventory Manager'),
            ('hr@nexora.com', 'admin12345', 'Claire', 'Chen', 'HR_MANAGER', 'Human Capital', '+1-555-0105', 'HR Director'),
            ('procure@nexora.com', 'admin12345', 'Raj', 'Patel', 'PROCUREMENT_MANAGER', 'Procurement', '+1-555-0106', 'Procurement Lead'),
            ('mfg@nexora.com', 'admin12345', 'Stefan', 'Lindqvist', 'EMPLOYEE', 'Advanced Manufacturing', '+1-555-0107', 'Manufacturing Lead'),
            ('support@nexora.com', 'admin12345', 'Sarah', 'Jenkins', 'SUPPORT_AGENT', 'Customer Success', '+1-555-0108', 'Support Lead'),
        ]

        users = {}
        for email, pwd, fname, lname, role, dept, phone, title in user_specs:
            u, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': fname,
                    'last_name': lname,
                    'role': role,
                    'department': dept,
                    'job_title': title,
                    'phone': phone,
                    'is_staff': True,
                    'is_superuser': (role == 'SUPER_ADMIN')
                }
            )
            if created or not u.check_password(pwd):
                u.set_password(pwd)
                u.job_title = title
                u.save()
            UserProfile.objects.get_or_create(user=u, defaults={'city': 'New York'})
            users[email] = u
        self.stdout.write(f'Created {len(users)} RBAC Enterprise Users')

        # 3. Chart of Accounts
        accounts_data = [
            ('1010', 'Cash on Hand', 'ASSET', Decimal('250000.00')),
            ('1020', 'Operating Checking Account - JPMorgan', 'ASSET', Decimal('1250000.00')),
            ('1050', 'Accounts Receivable (Trade)', 'ASSET', Decimal('420000.00')),
            ('1070', 'Allowance for Doubtful Accounts', 'ASSET', Decimal('-15000.00')),
            ('1200', 'Finished Goods Inventory', 'ASSET', Decimal('890000.00')),
            ('1210', 'Raw Materials & Components Inventory', 'ASSET', Decimal('340000.00')),
            ('1500', 'Manufacturing Plant & Machinery', 'ASSET', Decimal('2500000.00')),
            ('1510', 'Accumulated Depreciation - Machinery', 'ASSET', Decimal('-450000.00')),
            ('1600', 'Enterprise Fleet Vehicles', 'ASSET', Decimal('320000.00')),
            ('2010', 'Accounts Payable (Trade Suppliers)', 'LIABILITY', Decimal('380000.00')),
            ('2050', 'Accrued Payroll & Benefits Payable', 'LIABILITY', Decimal('125000.00')),
            ('2100', 'Sales Tax & VAT Payable', 'LIABILITY', Decimal('48000.00')),
            ('2500', 'Long Term Bank Credit Facility', 'LIABILITY', Decimal('1000000.00')),
            ('3010', 'Common Capital Stock', 'EQUITY', Decimal('2500000.00')),
            ('3020', 'Retained Earnings', 'EQUITY', Decimal('1152000.00')),
            ('4010', 'Commercial Hardware Systems Revenue', 'REVENUE', Decimal('850000.00')),
            ('4020', 'Enterprise Software Licensing Revenue', 'REVENUE', Decimal('420000.00')),
            ('4030', 'Professional Support & SLA Services', 'REVENUE', Decimal('180000.00')),
            ('5010', 'Cost of Goods Sold - Hardware', 'EXPENSE', Decimal('420000.00')),
            ('5020', 'Direct Manufacturing Labor', 'EXPENSE', Decimal('110000.00')),
            ('6010', 'Executive & Administrative Salaries', 'EXPENSE', Decimal('195000.00')),
            ('6020', 'Global Facility Rent & Utilities', 'EXPENSE', Decimal('85000.00')),
            ('6030', 'R&D Technology Infrastructure', 'EXPENSE', Decimal('62000.00')),
            ('6040', 'Corporate Marketing & Advertising', 'EXPENSE', Decimal('45000.00')),
        ]

        coa = {}
        for code, name, atype, bal in accounts_data:
            acc, _ = Account.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'account_type': atype,
                    'balance': bal,
                    'is_active': True
                }
            )
            coa[code] = acc
        self.stdout.write(f'Created {len(coa)} Chart of Accounts')

        # Bank Account Link
        bank_acc, _ = BankAccount.objects.get_or_create(
            gl_account=coa['1020'],
            defaults={
                'account_name': 'Operating Checking Account',
                'bank_name': 'JPMorgan Chase Enterprise Banking',
                'account_number': 'CHK-99283746102',
                'routing_number': '021000021',
                'currency': 'USD',
                'balance': Decimal('1250000.00')
            }
        )

        # 4. Inventory Catalog & UOM
        uom_ea, _ = UnitOfMeasure.objects.get_or_create(name='Unit / Each', defaults={'symbol': 'EA'})
        uom_kg, _ = UnitOfMeasure.objects.get_or_create(name='Kilogram', defaults={'symbol': 'KG'})
        uom_box, _ = UnitOfMeasure.objects.get_or_create(name='Master Carton Box', defaults={'symbol': 'BOX'})

        cat_hardware, _ = ProductCategory.objects.get_or_create(name='Enterprise Server Hardware', defaults={'code': 'CAT-HW'})
        cat_components, _ = ProductCategory.objects.get_or_create(name='Microcontroller Components', defaults={'code': 'CAT-COMP'})
        cat_raw, _ = ProductCategory.objects.get_or_create(name='Industrial Raw Materials', defaults={'code': 'CAT-RAW'})

        brand_nexora, _ = ProductBrand.objects.get_or_create(name='Nexora Titan Series')
        brand_quantum, _ = ProductBrand.objects.get_or_create(name='Quantum Silicon')

        products_info = [
            ('NX-9000-SRV', 'Nexora Titan NX-9000 Compute Cluster', cat_hardware, brand_nexora, uom_ea, Decimal('3200.00'), Decimal('6800.00'), Decimal('85.00'), 20),
            ('NX-7500-SRV', 'Nexora Titan NX-7500 Edge Server Node', cat_hardware, brand_nexora, uom_ea, Decimal('1800.00'), Decimal('3950.00'), Decimal('140.00'), 30),
            ('QS-MCU-800', 'Quantum Multi-Core MCU Processor Array', cat_components, brand_quantum, uom_ea, Decimal('120.00'), Decimal('290.00'), Decimal('650.00'), 100),
            ('QS-MOD-5G', 'Industrial 5G Telemetry Transceiver Module', cat_components, brand_quantum, uom_ea, Decimal('45.00'), Decimal('115.00'), Decimal('1200.00'), 200),
            ('ALU-CHAS-01', 'Aerospace Anodized Aluminum Chassis Block', cat_raw, brand_nexora, uom_ea, Decimal('85.00'), Decimal('180.00'), Decimal('450.00'), 50),
            ('OPT-FBR-100', 'Military-Grade Fiber Optic Harness (100m)', cat_components, brand_nexora, uom_box, Decimal('65.00'), Decimal('150.00'), Decimal('320.00'), 40),
        ]

        prods = {}
        for i, (sku, name, cat, brand, uom, cost, price, stock, reorder) in enumerate(products_info, start=1):
            p, _ = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name,
                    'category': cat,
                    'brand': brand,
                    'uom': uom,
                    'cost_price': cost,
                    'selling_price': price,
                    'current_stock': stock,
                    'reorder_level': reorder,
                    'barcode': f'89012345678{i:02d}',
                    'is_active': True
                }
            )
            prods[sku] = p

        # 5. Warehouse & Bins
        wh_ny, _ = Warehouse.objects.get_or_create(code='WH-NYC-01', defaults={'branch': branch_hq, 'name': 'New York Main Distribution Hub', 'city': 'New York', 'address': '100 Port Street', 'is_primary': True})
        wh_lon, _ = Warehouse.objects.get_or_create(code='WH-LON-02', defaults={'branch': branch_emea, 'name': 'London Logistics Terminal', 'city': 'London', 'address': 'Docklands Gate 4'})

        zone_a, _ = Zone.objects.get_or_create(warehouse=wh_ny, code='ZN-A', defaults={'name': 'High-Density Server Racks'})
        bin_a1, _ = Bin.objects.get_or_create(zone=zone_a, aisle='A01', shelf='S01', bin_number='B01', defaults={'max_weight_kg': Decimal('1000.00')})
        bin_a2, _ = Bin.objects.get_or_create(zone=zone_a, aisle='A01', shelf='S01', bin_number='B02', defaults={'max_weight_kg': Decimal('1000.00')})

        # Stock movements records
        for p in prods.values():
            StockMovement.objects.get_or_create(
                product=p,
                reference_number=f'INIT-{p.sku}',
                defaults={
                    'movement_type': 'PURCHASE_RECEIPT',
                    'quantity': p.current_stock,
                    'unit_cost': p.cost_price,
                    'total_cost': p.current_stock * p.cost_price,
                    'balance_after': p.current_stock,
                    'notes': 'Initial system warehouse stock intake',
                    'created_by': users['admin@nexora.com']
                }
            )

        # 6. CRM (Companies, Contacts, Leads, Opportunities)
        comp_apex, _ = Company.objects.get_or_create(name='Apex Aerospace & Defense', defaults={'industry': 'Aerospace', 'email': 'procure@apexaero.com', 'phone': '+1-800-444-9988', 'annual_revenue': Decimal('45000000.00'), 'city': 'Seattle'})
        comp_zenith, _ = Company.objects.get_or_create(name='Zenith Financial Cloud Systems', defaults={'industry': 'FinTech', 'email': 'tech@zenithcloud.io', 'phone': '+1-212-909-3322', 'annual_revenue': Decimal('28000000.00'), 'city': 'New York'})
        comp_omni, _ = Company.objects.get_or_create(name='OmniCorp Global Telecom', defaults={'industry': 'Telecommunications', 'email': 'contracts@omnicorp.net', 'phone': '+44-20-7946-0912', 'annual_revenue': Decimal('120000000.00'), 'city': 'London'})

        c1, _ = Contact.objects.get_or_create(company=comp_apex, email='d.halloway@apexaero.com', defaults={'first_name': 'David', 'last_name': 'Halloway', 'job_title': 'VP of Engineering', 'phone': '+1-555-401-2299'})
        c2, _ = Contact.objects.get_or_create(company=comp_zenith, email='r.mercer@zenithcloud.io', defaults={'first_name': 'Rachel', 'last_name': 'Mercer', 'job_title': 'Chief Technology Officer', 'phone': '+1-555-882-9011'})
        c3, _ = Contact.objects.get_or_create(company=comp_omni, email='a.becker@omnicorp.net', defaults={'first_name': 'Arthur', 'last_name': 'Becker', 'job_title': 'Director of Infrastructure', 'phone': '+44-7700-900123'})

        camp, _ = Campaign.objects.get_or_create(name='Q1 Enterprise Edge AI Hardware Summit', defaults={'campaign_type': 'TRADE_SHOW', 'budget': Decimal('35000.00'), 'start_date': date(2026, 1, 15), 'is_active': True})

        Lead.objects.get_or_create(email='g.morrison@solargrid.tech', defaults={'first_name': 'Gary', 'last_name': 'Morrison', 'company_name': 'SolarGrid Renewable Power', 'campaign': camp, 'status': 'QUALIFIED', 'assigned_to': users['sales@nexora.com'], 'estimated_budget': Decimal('180000.00')})
        Lead.objects.get_or_create(email='m.volkov@hyperrail.eu', defaults={'first_name': 'Mikhail', 'last_name': 'Volkov', 'company_name': 'HyperRail Autonomous Transit', 'status': 'CONTACTED', 'assigned_to': users['sales@nexora.com'], 'estimated_budget': Decimal('340000.00')})

        opp1, _ = Opportunity.objects.get_or_create(name='Apex Next-Gen Flight Simulator Compute Rack', defaults={'company': comp_apex, 'contact': c1, 'stage': 'PROPOSAL', 'amount': Decimal('480000.00'), 'probability': 75, 'expected_close_date': date.today() + timedelta(days=30), 'assigned_to': users['sales@nexora.com']})
        opp2, _ = Opportunity.objects.get_or_create(name='Zenith Low-Latency Trading Grid Infrastructure', defaults={'company': comp_zenith, 'contact': c2, 'stage': 'NEGOTIATION', 'amount': Decimal('750000.00'), 'probability': 90, 'expected_close_date': date.today() + timedelta(days=15), 'assigned_to': users['sales@nexora.com']})

        # 7. Customers & Sales Cycle (Quotations, Orders, Invoices, Payments)
        cust_apex, _ = Customer.objects.get_or_create(
            email='finance@apexaero.com',
            defaults={
                'company': comp_apex,
                'first_name': 'David',
                'last_name': 'Halloway',
                'company_name': 'Apex Aerospace & Defense',
                'phone': '+1-800-444-9988',
                'credit_limit': Decimal('1000000.00'),
                'billing_address': 'Building 40, Boeing Field, Seattle, WA',
                'tax_id': 'US-APEX-88291',
                'city': 'Seattle',
                'country': 'USA'
            }
        )
        cust_zenith, _ = Customer.objects.get_or_create(
            email='ap@zenithcloud.io',
            defaults={
                'company': comp_zenith,
                'first_name': 'Rachel',
                'last_name': 'Mercer',
                'company_name': 'Zenith Financial Cloud Systems',
                'phone': '+1-212-909-3322',
                'credit_limit': Decimal('1500000.00'),
                'billing_address': '450 Lexington Ave, New York, NY',
                'tax_id': 'US-ZEN-11029',
                'city': 'New York',
                'country': 'USA'
            }
        )

        # Sales Order 1: Apex Aerospace
        so1, _ = SalesOrder.objects.get_or_create(
            order_number='SO-2026-0001',
            defaults={
                'customer': cust_apex,
                'order_date': date.today() - timedelta(days=10),
                'subtotal': Decimal('136000.00'),
                'tax_amount': Decimal('11560.00'),
                'total_amount': Decimal('147560.00'),
                'status': 'DELIVERED',
                'created_by': users['sales@nexora.com']
            }
        )
        SalesOrderItem.objects.get_or_create(order=so1, product=prods['NX-9000-SRV'], defaults={'quantity': Decimal('20.00'), 'unit_price': Decimal('6800.00'), 'total': Decimal('136000.00')})

        # Invoice 1 & Payment
        inv1, _ = Invoice.objects.get_or_create(
            invoice_number='INV-2026-0001',
            defaults={
                'sales_order': so1,
                'customer': cust_apex,
                'invoice_date': date.today() - timedelta(days=8),
                'due_date': date.today() + timedelta(days=22),
                'subtotal': Decimal('136000.00'),
                'tax_amount': Decimal('11560.00'),
                'total_amount': Decimal('147560.00'),
                'paid_amount': Decimal('147560.00'),
                'balance_due': Decimal('0.00'),
                'status': 'PAID',
                'created_by': users['finance@nexora.com']
            }
        )
        InvoiceItem.objects.get_or_create(invoice=inv1, product=prods['NX-9000-SRV'], defaults={'quantity': Decimal('20.00'), 'unit_price': Decimal('6800.00'), 'total': Decimal('136000.00')})
        Payment.objects.get_or_create(payment_number='PAY-2026-0001', defaults={'invoice': inv1, 'customer': cust_apex, 'amount': Decimal('147560.00'), 'payment_method': 'BANK_TRANSFER', 'payment_date': date.today() - timedelta(days=5), 'reference_number': 'WIRE-JPM-88992', 'created_by': users['finance@nexora.com']})

        # Sales Order 2: Zenith Cloud
        so2, _ = SalesOrder.objects.get_or_create(
            order_number='SO-2026-0002',
            defaults={
                'customer': cust_zenith,
                'order_date': date.today() - timedelta(days=3),
                'subtotal': Decimal('118500.00'),
                'tax_amount': Decimal('10072.50'),
                'total_amount': Decimal('128572.50'),
                'status': 'CONFIRMED',
                'created_by': users['sales@nexora.com']
            }
        )
        SalesOrderItem.objects.get_or_create(order=so2, product=prods['NX-7500-SRV'], defaults={'quantity': Decimal('30.00'), 'unit_price': Decimal('3950.00'), 'total': Decimal('118500.00')})

        inv2, _ = Invoice.objects.get_or_create(
            invoice_number='INV-2026-0002',
            defaults={
                'sales_order': so2,
                'customer': cust_zenith,
                'invoice_date': date.today() - timedelta(days=2),
                'due_date': date.today() + timedelta(days=13),
                'subtotal': Decimal('118500.00'),
                'tax_amount': Decimal('10072.50'),
                'total_amount': Decimal('128572.50'),
                'paid_amount': Decimal('50000.00'),
                'balance_due': Decimal('78572.50'),
                'status': 'PARTIAL',
                'created_by': users['finance@nexora.com']
            }
        )
        Payment.objects.get_or_create(payment_number='PAY-2026-0002', defaults={'invoice': inv2, 'customer': cust_zenith, 'amount': Decimal('50000.00'), 'payment_method': 'CREDIT_CARD', 'payment_date': date.today() - timedelta(days=1), 'reference_number': 'CC-AUTH-77382', 'created_by': users['finance@nexora.com']})

        # 8. Suppliers & Purchasing (Purchase Orders, GRN)
        sup_silicon, _ = Supplier.objects.get_or_create(name='Silicon Micro Devices Corp', defaults={'contact_person': 'Kenji Sato', 'email': 'orders@siliconmicro.jp', 'phone': '+81-3-5555-0199', 'payment_terms': 'Net 30', 'rating': Decimal('4.8'), 'city': 'Tokyo', 'country': 'Japan', 'address': 'Shinjuku 2-chome'})
        sup_metals, _ = Supplier.objects.get_or_create(name='Precision Alloys & Chassis Ltd', defaults={'contact_person': 'Hans Zimmer', 'email': 'sales@precisionalloys.de', 'phone': '+49-89-123456', 'payment_terms': 'Net 60', 'rating': Decimal('4.6'), 'city': 'Munich', 'country': 'Germany', 'address': 'Industriestrasse 14'})

        po1, _ = PurchaseOrder.objects.get_or_create(
            po_number='PO-2026-0001',
            defaults={
                'supplier': sup_silicon,
                'order_date': date.today() - timedelta(days=14),
                'expected_delivery': date.today() - timedelta(days=4),
                'subtotal': Decimal('60000.00'),
                'tax_amount': Decimal('5100.00'),
                'total_amount': Decimal('65100.00'),
                'status': 'RECEIVED',
                'created_by': users['procure@nexora.com']
            }
        )
        PurchaseOrderItem.objects.get_or_create(order=po1, product=prods['QS-MCU-800'], defaults={'quantity': Decimal('500.00'), 'unit_price': Decimal('120.00'), 'total': Decimal('60000.00')})

        grn1, _ = GoodsReceiptNote.objects.get_or_create(
            grn_number='GRN-2026-0001',
            defaults={
                'purchase_order': po1,
                'warehouse': wh_ny,
                'receipt_date': date.today() - timedelta(days=4),
                'received_by': users['inventory@nexora.com'],
                'notes': 'All 500 units inspected and certified defect-free.'
            }
        )
        GoodsReceiptItem.objects.get_or_create(grn=grn1, product=prods['QS-MCU-800'], defaults={'quantity_received': Decimal('500.00')})

        # 9. General Ledger Accounting Journal Entries
        je1, _ = JournalEntry.objects.get_or_create(
            entry_number='JE-2026-0001',
            defaults={
                'date': date.today() - timedelta(days=8),
                'fiscal_year': fy,
                'reference': 'INV-2026-0001',
                'narration': 'Recognized revenue and AR for Apex Aerospace order SO-2026-0001',
                'total_debit': Decimal('147560.00'),
                'total_credit': Decimal('147560.00'),
                'status': 'POSTED',
                'created_by': users['finance@nexora.com'],
                'posted_at': timezone.now()
            }
        )
        JournalItem.objects.get_or_create(journal_entry=je1, account=coa['1050'], defaults={'debit': Decimal('147560.00'), 'credit': Decimal('0.00'), 'description': 'Trade AR Receivable'})
        JournalItem.objects.get_or_create(journal_entry=je1, account=coa['4010'], defaults={'debit': Decimal('0.00'), 'credit': Decimal('136000.00'), 'description': 'Hardware Systems Revenue'})
        JournalItem.objects.get_or_create(journal_entry=je1, account=coa['2100'], defaults={'debit': Decimal('0.00'), 'credit': Decimal('11560.00'), 'description': 'Sales Tax Payable'})

        je2, _ = JournalEntry.objects.get_or_create(
            entry_number='JE-2026-0002',
            defaults={
                'date': date.today() - timedelta(days=5),
                'fiscal_year': fy,
                'reference': 'PAY-2026-0001',
                'narration': 'Settled customer payment via JPMorgan Chase Bank Wire',
                'total_debit': Decimal('147560.00'),
                'total_credit': Decimal('147560.00'),
                'status': 'POSTED',
                'created_by': users['finance@nexora.com'],
                'posted_at': timezone.now()
            }
        )
        JournalItem.objects.get_or_create(journal_entry=je2, account=coa['1020'], defaults={'debit': Decimal('147560.00'), 'credit': Decimal('0.00'), 'description': 'JPMorgan Cash Inflow'})
        JournalItem.objects.get_or_create(journal_entry=je2, account=coa['1050'], defaults={'debit': Decimal('0.00'), 'credit': Decimal('147560.00'), 'description': 'Relieve Trade AR'})

        # 10. HR, Designations, Attendance & Payroll
        des_ceo, _ = Designation.objects.get_or_create(code='DES-CEO', defaults={'title': 'Chief Executive Officer', 'department': dept_exec})
        des_vp_sales, _ = Designation.objects.get_or_create(code='DES-VPSALES', defaults={'title': 'VP of Commercial Sales', 'department': dept_sales})
        des_cfo, _ = Designation.objects.get_or_create(code='DES-CFO', defaults={'title': 'Chief Financial Officer', 'department': dept_fin})
        des_eng_lead, _ = Designation.objects.get_or_create(code='DES-ENGLEAD', defaults={'title': 'Lead Systems Architect', 'department': dept_eng})
        des_hr_dir, _ = Designation.objects.get_or_create(code='DES-HRDIR', defaults={'title': 'Director of People Operations', 'department': dept_hr})
        des_driver, _ = Designation.objects.get_or_create(code='DES-DRIVER', defaults={'title': 'Fleet Logistics Driver', 'department': dept_scm})

        emp_vance, _ = Employee.objects.get_or_create(employee_id='EMP-001', defaults={'user': users['admin@nexora.com'], 'first_name': 'Alexander', 'last_name': 'Vance', 'email': 'admin@nexora.com', 'phone': '+1-555-0101', 'designation': des_ceo, 'department': dept_exec, 'branch': branch_hq, 'joining_date': date(2022, 1, 10), 'status': 'ACTIVE'})
        emp_elena, _ = Employee.objects.get_or_create(employee_id='EMP-002', defaults={'user': users['sales@nexora.com'], 'first_name': 'Elena', 'last_name': 'Rostova', 'email': 'sales@nexora.com', 'phone': '+1-555-0102', 'designation': des_vp_sales, 'department': dept_sales, 'branch': branch_hq, 'joining_date': date(2022, 6, 15), 'status': 'ACTIVE'})
        emp_marcus, _ = Employee.objects.get_or_create(employee_id='EMP-003', defaults={'user': users['finance@nexora.com'], 'first_name': 'Marcus', 'last_name': 'Sterling', 'email': 'finance@nexora.com', 'phone': '+1-555-0103', 'designation': des_cfo, 'department': dept_fin, 'branch': branch_hq, 'joining_date': date(2023, 2, 1), 'status': 'ACTIVE'})
        emp_claire, _ = Employee.objects.get_or_create(employee_id='EMP-004', defaults={'user': users['hr@nexora.com'], 'first_name': 'Claire', 'last_name': 'Chen', 'email': 'hr@nexora.com', 'phone': '+1-555-0105', 'designation': des_hr_dir, 'department': dept_hr, 'branch': branch_hq, 'joining_date': date(2023, 4, 1), 'status': 'ACTIVE'})

        # Attendance log
        for emp in [emp_vance, emp_elena, emp_marcus, emp_claire]:
            for d in range(1, 6):
                log_date = date.today() - timedelta(days=d)
                if log_date.weekday() < 5:  # Weekday
                    Attendance.objects.get_or_create(
                        employee=emp,
                        date=log_date,
                        defaults={
                            'status': 'PRESENT',
                            'check_in': '08:55:00',
                            'check_out': '17:30:00',
                            'work_hours': Decimal('8.50')
                        }
                    )

        # Leave Types & Requests
        lt_annual, _ = LeaveType.objects.get_or_create(code='LT-ANNUAL', defaults={'name': 'Annual Paid Leave', 'days_allowed_per_year': 24, 'is_paid': True})
        LeaveRequest.objects.get_or_create(
            employee=emp_elena,
            leave_type=lt_annual,
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=24),
            defaults={'total_days': 5, 'reason': 'Executive holiday recess', 'status': 'APPROVED'}
        )

        # Salary Structure & Monthly Payrun
        for emp in [emp_vance, emp_elena, emp_marcus, emp_claire]:
            SalaryStructure.objects.get_or_create(
                employee=emp,
                defaults={
                    'basic_salary': Decimal('12000.00'),
                    'hra_allowance': Decimal('1800.00'),
                    'transport_allowance': Decimal('800.00'),
                    'medical_allowance': Decimal('300.00'),
                    'special_allowance': Decimal('500.00'),
                    'provident_fund': Decimal('400.00'),
                    'tax_deduction': Decimal('2160.00'),
                }
            )

        payrun, _ = Payrun.objects.get_or_create(
            title='Payroll February 2026',
            month=2,
            year=2026,
            defaults={
                'start_date': date(2026, 2, 1),
                'end_date': date(2026, 2, 28),
                'total_gross': Decimal('73450.00'),
                'total_deductions': Decimal('13221.00'),
                'total_net': Decimal('60229.00'),
                'status': 'PAID',
                'processed_by': users['hr@nexora.com']
            }
        )
        for emp in [emp_vance, emp_elena, emp_marcus, emp_claire]:
            Payslip.objects.get_or_create(
                payrun=payrun,
                employee=emp,
                defaults={
                    'basic_salary': Decimal('12000.00'),
                    'allowances': Decimal('3400.00'),
                    'gross_salary': Decimal('15400.00'),
                    'deductions': Decimal('2560.00'),
                    'net_salary': Decimal('12840.00'),
                    'is_paid': True
                }
            )

        # 11. Projects, Milestones, Tasks & Timesheets
        proj1, _ = Project.objects.get_or_create(
            code='PRJ-CLOUDERP',
            defaults={
                'name': 'Nexora Enterprise OS Core Modernization',
                'description': 'End-to-end modernization of enterprise core business engines',
                'client': comp_apex,
                'project_manager': users['admin@nexora.com'],
                'budget': Decimal('250000.00'),
                'actual_cost': Decimal('115000.00'),
                'start_date': date(2026, 1, 5),
                'end_date': date(2026, 6, 30),
                'status': 'ACTIVE',
                'priority': 'HIGH',
                'progress_percentage': 65
            }
        )
        ms1, _ = Milestone.objects.get_or_create(project=proj1, title='Sprint 4 - Realtime Financial Engines', defaults={'due_date': date.today() + timedelta(days=10), 'is_completed': True})
        task1, _ = Task.objects.get_or_create(project=proj1, title='Implement Double-Entry Journal Auto-Balancing', defaults={'milestone': ms1, 'assigned_to': users['finance@nexora.com'], 'priority': 'HIGH', 'status': 'DONE', 'estimated_hours': Decimal('24.00'), 'actual_hours': Decimal('22.50'), 'due_date': date.today() + timedelta(days=5)})
        Timesheet.objects.get_or_create(task=task1, employee=emp_marcus, date=date.today() - timedelta(days=2), defaults={'hours': Decimal('8.00'), 'description': 'Completed accounting ledger reconciliation service', 'is_billable': True})

        # 12. Support & Helpdesk
        cat_tech, _ = TicketCategory.objects.get_or_create(name='Technical System Architecture', defaults={'sla_response_hours': 4, 'sla_resolution_hours': 24})
        ticket1, _ = SupportTicket.objects.get_or_create(
            ticket_id='TIK-2026-1001',
            defaults={
                'customer': cust_apex,
                'category': cat_tech,
                'subject': 'High-Throughput Transceiver Firmware Synchronization',
                'description': 'Requesting hardware diagnostic profile update for NX-9000 cluster.',
                'priority': 'HIGH',
                'status': 'IN_PROGRESS',
                'assigned_to': users['support@nexora.com']
            }
        )
        TicketComment.objects.get_or_create(ticket=ticket1, author=users['support@nexora.com'], defaults={'comment': 'Engineering has dispatched the patch firmware build 4.2.1-prod.', 'is_internal_note': False})

        # 13. Fixed Assets & Fleet
        cat_machinery, _ = AssetCategory.objects.get_or_create(name='Precision Manufacturing SMT Machinery', defaults={'depreciation_method': 'STRAIGHT_LINE', 'useful_life_years': 7, 'salvage_value_percentage': Decimal('10.00')})
        asset1, _ = Asset.objects.get_or_create(
            asset_tag='AST-SMT-001',
            defaults={
                'name': 'Titan High-Speed SMT Surface Mount Assembler',
                'category': cat_machinery,
                'serial_number': 'SN-SMT-998822-DE',
                'purchase_date': date(2024, 3, 15),
                'purchase_cost': Decimal('450000.00'),
                'current_value': Decimal('325000.00'),
                'salvage_value': Decimal('45000.00'),
                'status': 'ASSIGNED',
                'location': 'London Manufacturing Bay 2'
            }
        )
        AssetMaintenanceLog.objects.get_or_create(asset=asset1, date=date.today() - timedelta(days=20), defaults={'service_type': 'PREVENTIVE', 'cost': Decimal('3200.00'), 'service_provider': 'Siemens Industrial Diagnostics', 'notes': 'Precision calibration and optical lens alignment'})

        # Driver linked to employee
        driver_emp, _ = Employee.objects.get_or_create(employee_id='EMP-005', defaults={'first_name': 'Robert', 'last_name': 'Jackson', 'email': 'r.jackson@nexora.com', 'phone': '+1-555-883-1122', 'designation': des_driver, 'department': dept_scm, 'branch': branch_hq, 'joining_date': date(2023, 8, 1), 'status': 'ACTIVE'})
        driver1, _ = Driver.objects.get_or_create(employee=driver_emp, defaults={'license_number': 'DL-NY-998231', 'license_expiry': date(2028, 12, 31), 'is_available': True})
        veh1, _ = Vehicle.objects.get_or_create(plate_number='NYC-ERP-991', defaults={'make': 'Mercedes-Benz', 'model': 'Sprinter Cargo Van', 'year': 2024, 'fuel_type': 'DIESEL', 'current_odometer_km': 18400, 'status': 'AVAILABLE', 'assigned_driver': driver1})
        FuelLog.objects.get_or_create(vehicle=veh1, date=date.today() - timedelta(days=3), defaults={'liters': Decimal('65.00'), 'cost_per_liter': Decimal('1.45'), 'total_cost': Decimal('94.25'), 'odometer_km': 18320, 'station': 'Shell Fleet Station NYC'})

        # 14. Advanced Manufacturing & BOM
        wc1, _ = WorkCenter.objects.get_or_create(code='WC-SMT-01', defaults={'name': 'High Precision SMT Assembly Cell', 'hourly_rate': Decimal('85.00'), 'capacity_hours_per_day': Decimal('16.00')})
        wc2, _ = WorkCenter.objects.get_or_create(code='WC-QA-02', defaults={'name': 'Thermal & Stress Inspection Cell', 'hourly_rate': Decimal('65.00'), 'capacity_hours_per_day': Decimal('8.00')})

        bom1, _ = BillOfMaterials.objects.get_or_create(
            bom_number='BOM-NX9000',
            defaults={'finished_product': prods['NX-9000-SRV'], 'quantity': Decimal('1.00'), 'is_active': True}
        )
        BOMItem.objects.get_or_create(bom=bom1, raw_material=prods['QS-MCU-800'], defaults={'quantity': Decimal('8.00')})
        BOMItem.objects.get_or_create(bom=bom1, raw_material=prods['QS-MOD-5G'], defaults={'quantity': Decimal('2.00')})
        BOMItem.objects.get_or_create(bom=bom1, raw_material=prods['ALU-CHAS-01'], defaults={'quantity': Decimal('1.00')})
        BOMItem.objects.get_or_create(bom=bom1, raw_material=prods['OPT-FBR-100'], defaults={'quantity': Decimal('2.00')})

        mo1, _ = ProductionOrder.objects.get_or_create(
            order_number='MO-2026-0001',
            defaults={
                'bom': bom1,
                'work_center': wc1,
                'quantity_to_produce': Decimal('25.00'),
                'start_date': date.today() - timedelta(days=12),
                'due_date': date.today() - timedelta(days=2),
                'status': 'COMPLETED',
                'created_by': users['admin@nexora.com']
            }
        )

        # 15. Documents & Workflows
        folder_fin, _ = Folder.objects.get_or_create(name='Corporate Finance & Audit Reports', defaults={'created_by': users['finance@nexora.com']})
        folder_eng, _ = Folder.objects.get_or_create(name='Hardware Engineering Specifications', defaults={'created_by': users['admin@nexora.com']})

        Document.objects.get_or_create(
            title='Nexora Titan NX-9000 Hardware Architecture Whitepaper',
            defaults={
                'folder': folder_eng,
                'version': 1,
                'description': 'Master hardware technical specification and schematic references.',
                'uploaded_by': users['admin@nexora.com']
            }
        )

        wf_po, _ = WorkflowDefinition.objects.get_or_create(
            module_type='PURCHASE_ORDER',
            defaults={
                'name': 'Executive Purchase Order Approval Workflow',
                'description': 'Tiered approval for purchase requisitions exceeding $10,000 threshold.',
                'is_active': True,
                'auto_escalate_hours': 48
            }
        )
        WorkflowStage.objects.get_or_create(workflow=wf_po, step_number=1, defaults={'name': 'Procurement Manager Sign-Off', 'required_role': 'PROCUREMENT_MANAGER', 'threshold_amount': Decimal('10000.00')})
        WorkflowStage.objects.get_or_create(workflow=wf_po, step_number=2, defaults={'name': 'CFO Financial Authorization', 'required_role': 'ACCOUNTANT', 'threshold_amount': Decimal('50000.00')})

        # 16. System Settings & Integration Adapters
        SystemSetting.objects.get_or_create(key='ENTERPRISE_SYSTEM_NAME', defaults={'value': 'Nexora Enterprise OS', 'description': 'Branded master name for ERP deployment', 'is_public': True})
        SystemSetting.objects.get_or_create(key='AUTO_POST_GL_JOURNALS', defaults={'value': 'true', 'description': 'Automatically create double-entry journal records on invoice creation and payment', 'is_public': False})
        SystemSetting.objects.get_or_create(key='STRICT_INVENTORY_VALUATION', defaults={'value': 'PERPETUAL_WEIGHTED_AVERAGE', 'description': 'Perpetual cost valuation calculation method', 'is_public': False})

        IntegrationConfig.objects.get_or_create(provider_code='JPMORGAN_GATEWAY', defaults={'name': 'JPMorgan ACH & Wire Gateway', 'is_active': True, 'extra_config': {'merchant_id': 'JPM-MERCH-88392'}})
        IntegrationConfig.objects.get_or_create(provider_code='FEDEX_TRACKING', defaults={'name': 'FedEx Freight & Logistics Tracking API', 'is_active': True, 'extra_config': {'account_number': 'FDX-773829'}})
        IntegrationConfig.objects.get_or_create(provider_code='SENDGRID_SMTP', defaults={'name': 'SendGrid Enterprise Transactional Mail', 'is_active': True, 'extra_config': {'api_host': 'smtp.sendgrid.net'}})

        # 17. Initial Broadcast Notifications
        Notification.objects.get_or_create(
            recipient=users['admin@nexora.com'],
            title='Fiscal Period FY 2026 Initialized',
            defaults={
                'message': 'All 24 business modules are fully online with real-time General Ledger integration enabled.',
                'priority': 'NORMAL',
                'category': 'SYSTEM',
                'link': '/dashboard/'
            }
        )
        Notification.objects.get_or_create(
            recipient=users['admin@nexora.com'],
            title='Executive Sales Order Delivered: Apex Aerospace',
            defaults={
                'message': 'Sales Order SO-2026-0001 ($147,560.00) fully fulfilled and payment settled.',
                'priority': 'NORMAL',
                'category': 'SALES',
                'link': '/sales/orders/1/'
            }
        )

        # 18. Point of Sale (POS) Terminals & Retail Masters
        terminal_main, _ = POSTerminal.objects.get_or_create(
            terminal_code='POS-TRM-01',
            defaults={
                'name': 'Main Flagship Checkout Counter 1',
                'branch': branch_hq,
                'warehouse': wh_ny,
                'ip_address': '192.168.1.101',
                'status': 'ACTIVE',
                'receipt_header': 'Nexora Enterprise Flagship NYC\nOne World Trade Center',
                'receipt_footer': 'Thank you for shopping with us!\nExchange within 30 days.'
            }
        )
        terminal_express, _ = POSTerminal.objects.get_or_create(
            terminal_code='POS-TRM-02',
            defaults={
                'name': 'Express Mobile Kiosk 2',
                'branch': branch_hq,
                'warehouse': wh_ny,
                'ip_address': '192.168.1.102',
                'status': 'ACTIVE'
            }
        )

        coupon_welcome, _ = POSCouponPromotion.objects.get_or_create(
            code='NEXORA10',
            defaults={
                'name': '10% Enterprise Loyalty Welcome',
                'discount_type': 'PERCENT',
                'discount_value': Decimal('10.00'),
                'min_order_value': Decimal('100.00'),
                'max_discount_cap': Decimal('50.00'),
                'valid_from': timezone.now() - timedelta(days=30),
                'valid_to': timezone.now() + timedelta(days=365),
                'usage_limit': 5000,
                'is_active': True
            }
        )

        # 19. Global Multi-Country Tax Localizations
        tax_in, _ = TaxJurisdiction.objects.get_or_create(
            code='IN-GST',
            defaults={
                'country': 'IN',
                'name': 'India Central & State GST',
                'tax_authority_name': 'Goods and Services Tax Network (GSTN)',
                'filing_frequency': 'MONTHLY',
                'currency': 'INR',
                'is_default': True,
                'e_invoicing_mandatory': True,
                'e_way_bill_mandatory': True,
                'e_way_bill_threshold': Decimal('50000.00')
            }
        )
        tax_us, _ = TaxJurisdiction.objects.get_or_create(
            code='US-SALES',
            defaults={
                'country': 'US',
                'name': 'United States State & Local Sales Tax',
                'tax_authority_name': 'State Department of Taxation & Finance',
                'filing_frequency': 'QUARTERLY',
                'currency': 'USD'
            }
        )

        # HSN / SAC Codes
        hsn_hardware, _ = HSNSACCode.objects.get_or_create(
            code='84713010',
            defaults={
                'description': 'Personal computers, laptops and microcomputers',
                'code_type': 'HSN',
                'standard_gst_rate': Decimal('18.00')
            }
        )
        hsn_software, _ = HSNSACCode.objects.get_or_create(
            code='998314',
            defaults={
                'description': 'Information technology and software design/consulting services',
                'code_type': 'SAC',
                'standard_gst_rate': Decimal('18.00')
            }
        )

        # US State Nexus
        USStateNexusRate.objects.get_or_create(
            state_code='NY',
            defaults={
                'state_name': 'New York',
                'state_sales_tax_rate': Decimal('4.00'),
                'avg_local_sales_tax_rate': Decimal('4.50'),
                'economic_nexus_revenue_threshold': Decimal('500000.00'),
                'has_physical_nexus': True,
                'has_economic_nexus': True
            }
        )
        USStateNexusRate.objects.get_or_create(
            state_code='CA',
            defaults={
                'state_name': 'California',
                'state_sales_tax_rate': Decimal('7.25'),
                'avg_local_sales_tax_rate': Decimal('1.75'),
                'economic_nexus_revenue_threshold': Decimal('500000.00'),
                'has_physical_nexus': False,
                'has_economic_nexus': True
            }
        )

        # EU VAT OSS Rules
        EUVATRule.objects.get_or_create(
            member_state_code='DE',
            defaults={
                'country_name': 'Germany',
                'standard_vat_rate': Decimal('19.00'),
                'reduced_vat_rate': Decimal('7.00'),
                'oss_scheme_enabled': True,
                'reverse_charge_b2b': True
            }
        )
        EUVATRule.objects.get_or_create(
            member_state_code='FR',
            defaults={
                'country_name': 'France',
                'standard_vat_rate': Decimal('20.00'),
                'reduced_vat_rate': Decimal('5.50'),
                'oss_scheme_enabled': True,
                'reverse_charge_b2b': True
            }
        )

        # 20. Bank Reconciliation Rules
        ReconciliationRule.objects.get_or_create(
            name='Auto-Match Exact Date & Amount',
            defaults={
                'priority': 1,
                'rule_type': 'EXACT_AMOUNT_AND_DATE',
                'min_confidence_score': 95,
                'is_active': True
            }
        )
        ReconciliationRule.objects.get_or_create(
            name='Auto-Match Customer Payment Reference',
            defaults={
                'priority': 2,
                'rule_type': 'AMOUNT_AND_REF',
                'min_confidence_score': 90,
                'is_active': True
            }
        )
        ReconciliationRule.objects.get_or_create(
            name='Bank Service Fee Auto-Adjustment',
            defaults={
                'priority': 3,
                'rule_type': 'DESCRIPTION_REGEX',
                'regex_pattern': 'BANK CHARGE|MONTHLY FEE|WIRE FEE|SERVICE CHG',
                'contra_account': Account.objects.filter(account_type='EXPENSE', name__icontains='Expense').first(),
                'auto_post_adjusting_entry': True,
                'min_confidence_score': 85,
                'is_active': True
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded enterprise demonstration data across all 27 modules!'))

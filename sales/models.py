from django.db import models
from django.conf import settings
from decimal import Decimal
from inventory.models import Product
from crm.models import Company

class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_customers')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    billing_address = models.CharField(max_length=255)
    shipping_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='United States')
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=50000.00)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        full = f"{self.first_name} {self.last_name}"
        if self.company_name:
            return f"{full} ({self.company_name})"
        return full

class Quotation(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent to Client'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]

    quote_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='quotations')
    date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    terms = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"Quote #{self.quote_number} - {self.customer} (${self.total_amount:,.2f})"

class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        gross = self.quantity * self.unit_price
        disc = gross * (Decimal(str(self.discount_percent)) / Decimal('100.0'))
        self.total = gross - disc
        super().save(*args, **kwargs)

class SalesOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed & Processing'),
        ('SHIPPED', 'Goods Shipped'),
        ('DELIVERED', 'Delivered'),
        ('INVOICED', 'Fully Invoiced'),
        ('CANCELLED', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    quotation = models.ForeignKey(Quotation, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales_orders')
    order_date = models.DateField()
    delivery_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-order_date', '-id']

    def __str__(self):
        return f"SO #{self.order_number} - {self.customer} (${self.total_amount:,.2f})"

class SalesOrderItem(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        gross = self.quantity * self.unit_price
        disc = gross * (Decimal(str(self.discount_percent)) / Decimal('100.0'))
        self.total = gross - disc
        super().save(*args, **kwargs)

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ISSUED', 'Issued / Unpaid'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices')
    invoice_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    balance_due = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    payment_terms = models.CharField(max_length=50, default='Net 30')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-invoice_date', '-id']

    def __str__(self):
        return f"INV #{self.invoice_number} - {self.customer} (${self.total_amount:,.2f})"

    def update_balance(self):
        self.balance_due = self.total_amount - self.paid_amount
        if self.balance_due <= Decimal('0.00'):
            self.status = 'PAID'
        elif self.paid_amount > Decimal('0.00'):
            self.status = 'PARTIAL'
        self.save(update_fields=['paid_amount', 'balance_due', 'status'])

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

class Payment(models.Model):
    METHOD_CHOICES = [
        ('BANK_TRANSFER', 'Bank Wire Transfer'),
        ('CREDIT_CARD', 'Credit Card / Stripe'),
        ('CHECK', 'Company Cheque'),
        ('CASH', 'Cash'),
        ('ACH', 'ACH Transfer'),
    ]

    payment_number = models.CharField(max_length=50, unique=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=METHOD_CHOICES, default='BANK_TRANSFER')
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment #{self.payment_number}: ${self.amount:,.2f} for INV #{self.invoice.invoice_number}"

class CreditNote(models.Model):
    credit_note_number = models.CharField(max_length=50, unique=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='credit_notes')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    issue_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=[('DRAFT', 'Draft'), ('APPLIED', 'Applied'), ('REFUNDED', 'Refunded')], default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Credit Note #{self.credit_note_number}: ${self.amount:,.2f}"

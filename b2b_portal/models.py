from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from organizations.models import Organization
from sales.models import Customer, Quotation, SalesOrder, Invoice, Payment
from inventory.models import Product
from crm.models import Contact

class B2BAccount(models.Model):
    PAYMENT_TERMS_CHOICES = [
        ('NET15', 'Net 15 Days'),
        ('NET30', 'Net 30 Days'),
        ('NET60', 'Net 60 Days'),
        ('NET90', 'Net 90 Days'),
        ('DUE_ON_RECEIPT', 'Due Upon Receipt'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='b2b_accounts')
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='b2b_profile')
    account_number = models.CharField(max_length=50, unique=True)
    primary_contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='b2b_accounts')
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('50000.00'))
    credit_balance_used = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES, default='NET30')
    discount_tier_name = models.CharField(max_length=100, default='Standard Wholesale Tier')
    tax_exemption_number = models.CharField(max_length=100, blank=True)
    portal_access_enabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.name} ({self.account_number})"

    @property
    def available_credit(self):
        return max(Decimal('0.00'), self.credit_limit - self.credit_balance_used)

    @property
    def credit_utilization_pct(self):
        if self.credit_limit > 0:
            return round((self.credit_balance_used / self.credit_limit) * Decimal('100.0'), 1)
        return Decimal('0.0')


class B2BCatalogPriceTier(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='b2b_price_tiers')
    b2b_account = models.ForeignKey(B2BAccount, on_delete=models.CASCADE, null=True, blank=True, related_name='custom_price_tiers', help_text='Null applies globally to all B2B accounts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='b2b_price_tiers')
    min_quantity = models.PositiveIntegerField(default=1)
    tier_unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    effective_from = models.DateField(default=timezone.now)
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['product', 'min_quantity']

    def __str__(self):
        account_label = self.b2b_account.account_number if self.b2b_account else 'Global B2B'
        return f"{self.product.name} ({account_label}) - Min {self.min_quantity} @ {self.tier_unit_price}"


class QuoteApprovalRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Customer Decision'),
        ('APPROVED', 'Approved by Buyer'),
        ('REJECTED', 'Rejected by Buyer'),
        ('EXPIRED', 'Offer Expired'),
        ('CONVERTED', 'Converted to Sales Order'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='quote_approvals')
    b2b_account = models.ForeignKey(B2BAccount, on_delete=models.CASCADE, related_name='quote_approvals')
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='b2b_approval_requests')
    request_token = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    customer_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='decided_b2b_quotes')
    resulting_sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='b2b_source_quote')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Quote #{self.quotation.quote_number} - {self.get_status_display()}"


class SelfServiceOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('PROCESSING', 'Processing in Warehouse'),
        ('SHIPPED', 'Dispatched / Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='b2b_self_orders')
    b2b_account = models.ForeignKey(B2BAccount, on_delete=models.CASCADE, related_name='self_orders')
    order_number = models.CharField(max_length=50, unique=True)
    po_reference_number = models.CharField(max_length=100, help_text='Buyer Internal PO Number')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    subtotal_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    shipping_address = models.TextField()
    billing_address = models.TextField()
    requested_delivery_date = models.DateField()
    shipping_carrier = models.CharField(max_length=100, blank=True, default='Standard Freight Delivery')
    tracking_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    sales_order = models.OneToOneField(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='b2b_portal_order')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"B2B Order {self.order_number} ({self.b2b_account.customer.name})"


class SelfServiceOrderItem(models.Model):
    order = models.ForeignKey(SelfServiceOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='b2b_order_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class DigitalPaymentTransaction(models.Model):
    GATEWAY_CHOICES = [
        ('STRIPE', 'Stripe Enterprise Connect'),
        ('PAYPAL', 'PayPal B2B Checkout'),
        ('ACH_TRANSFER', 'Direct Bank ACH Transfer'),
        ('WIRE_TRANSFER', 'Corporate Wire Transfer'),
        ('CORPORATE_CARD', 'Commercial Credit Card'),
    ]

    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('AUTHORIZED', 'Authorized'),
        ('CAPTURED', 'Captured / Paid'),
        ('FAILED', 'Failed / Declined'),
        ('REFUNDED', 'Refunded'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='b2b_payments')
    b2b_account = models.ForeignKey(B2BAccount, on_delete=models.CASCADE, related_name='digital_payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='b2b_digital_payments')
    transaction_reference = models.CharField(max_length=64, unique=True)
    payment_gateway = models.CharField(max_length=30, choices=GATEWAY_CHOICES, default='STRIPE')
    gateway_transaction_id = models.CharField(max_length=128, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INITIATED')
    posted_gl_payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='digital_gateway_tx')
    receipt_url = models.URLField(blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_reference} - {self.amount} {self.currency} ({self.status})"

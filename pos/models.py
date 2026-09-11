from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid


class POSTerminal(models.Model):
    TERMINAL_STATUS = [
        ('ACTIVE', 'Active / In-Service'),
        ('INACTIVE', 'Inactive / Closed'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('LOCKED', 'Security Locked'),
    ]

    terminal_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    branch = models.ForeignKey('organizations.Branch', on_delete=models.CASCADE, related_name='pos_terminals')
    warehouse = models.ForeignKey('warehouse.Warehouse', on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_terminals')
    cash_account = models.ForeignKey('accounting.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_terminals_cash')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=50, blank=True)
    receipt_header = models.TextField(blank=True, default='Nexora Enterprise Retail\nThank you for shopping with us!')
    receipt_footer = models.TextField(blank=True, default='Goods once sold can be exchanged within 7 days.\nVisit us at www.nexora-erp.io')
    allow_offline_orders = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=TERMINAL_STATUS, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['branch', 'terminal_code']
        verbose_name = 'POS Terminal'
        verbose_name_plural = 'POS Terminals'

    def __str__(self):
        return f"{self.terminal_code} - {self.name} ({self.branch.name})"


class POSSession(models.Model):
    SESSION_STATUS = [
        ('OPEN', 'Open'),
        ('PAUSED', 'Paused'),
        ('CLOSED', 'Closed & Reconciled'),
    ]

    session_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    terminal = models.ForeignKey(POSTerminal, on_delete=models.PROTECT, related_name='sessions')
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='pos_sessions')
    opening_time = models.DateTimeField(auto_now_add=True)
    closing_time = models.DateTimeField(null=True, blank=True)
    opening_cash = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    expected_cash = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    counted_cash = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    cash_difference = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_sales_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_orders_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='OPEN')
    opening_notes = models.TextField(blank=True)
    closing_notes = models.TextField(blank=True)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='closed_pos_sessions')

    class Meta:
        ordering = ['-opening_time']
        verbose_name = 'POS Session'
        verbose_name_plural = 'POS Sessions'

    def __str__(self):
        return f"Session {self.session_number} - {self.terminal.name} ({self.status})"


class POSCustomerLoyalty(models.Model):
    TIER_CHOICES = [
        ('BRONZE', 'Bronze Tier'),
        ('SILVER', 'Silver Tier (5% extra points)'),
        ('GOLD', 'Gold Tier (10% extra points)'),
        ('PLATINUM', 'Platinum VIP (20% extra points)'),
    ]

    customer = models.OneToOneField('sales.Customer', on_delete=models.CASCADE, related_name='pos_loyalty')
    card_number = models.CharField(max_length=64, unique=True, blank=True, null=True)
    points_balance = models.PositiveIntegerField(default=0)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='BRONZE')
    lifetime_points_earned = models.PositiveIntegerField(default=0)
    lifetime_points_redeemed = models.PositiveIntegerField(default=0)
    lifetime_spend = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    last_activity_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Customer Loyalty Card'
        verbose_name_plural = 'Customer Loyalty Cards'

    def __str__(self):
        return f"Loyalty: {self.customer.name} ({self.tier} - {self.points_balance} pts)"


class POSCouponPromotion(models.Model):
    DISCOUNT_TYPES = [
        ('PERCENT', 'Percentage Discount'),
        ('FIXED', 'Fixed Currency Amount'),
        ('BUY_X_GET_Y', 'Buy X Get Y Free'),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='PERCENT')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    max_discount_cap = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="0 for no limit")
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=1000)
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-valid_to']
        verbose_name = 'POS Coupon / Promo'
        verbose_name_plural = 'POS Coupons & Promotions'

    def __str__(self):
        return f"{self.code} - {self.name} ({self.discount_value})"


class POSOrder(models.Model):
    ORDER_TYPES = [
        ('RETAIL', 'Walk-in Retail'),
        ('TAKEAWAY', 'Takeaway'),
        ('DINE_IN', 'Dine-In Restaurant'),
        ('DELIVERY', 'Express Delivery'),
    ]

    ORDER_STATUS = [
        ('DRAFT', 'Draft Cart'),
        ('COMPLETED', 'Completed & Paid'),
        ('VOIDED', 'Voided / Cancelled'),
        ('REFUNDED', 'Returned / Refunded'),
    ]

    order_number = models.CharField(max_length=64, unique=True)
    session = models.ForeignKey(POSSession, on_delete=models.PROTECT, related_name='orders')
    terminal = models.ForeignKey(POSTerminal, on_delete=models.PROTECT, related_name='orders')
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='pos_orders')
    customer = models.ForeignKey('sales.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_orders')
    coupon = models.ForeignKey(POSCouponPromotion, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='RETAIL')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='COMPLETED')

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    roundoff_amount = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    change_returned = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    loyalty_points_earned = models.PositiveIntegerField(default=0)
    loyalty_points_redeemed = models.PositiveIntegerField(default=0)
    loyalty_discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'POS Order Receipt'
        verbose_name_plural = 'POS Order Receipts'

    def __str__(self):
        return f"{self.order_number} - {self.grand_total} ({self.status})"


class POSOrderItem(models.Model):
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT, related_name='pos_order_items')
    product_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('1.000'))
    tax_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'POS Order Item'
        verbose_name_plural = 'POS Order Items'

    def __str__(self):
        return f"{self.product_name} x {self.quantity} = {self.line_total}"


class POSPayment(models.Model):
    PAYMENT_METHODS = [
        ('CASH', 'Cash Counter'),
        ('CREDIT_CARD', 'Credit / Debit Card'),
        ('UPI_QR', 'UPI / QR Code Instant'),
        ('WALLET', 'Digital Wallet (ApplePay/GooglePay)'),
        ('LOYALTY', 'Loyalty Points Redemption'),
        ('STORE_CREDIT', 'Store Credit / Gift Card'),
    ]

    PAYMENT_STATUS = [
        ('SUCCESS', 'Successful'),
        ('FAILED', 'Failed / Declined'),
        ('REFUNDED', 'Refunded'),
    ]

    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name='payments')
    session = models.ForeignKey(POSSession, on_delete=models.PROTECT, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference_number = models.CharField(max_length=100, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_network = models.CharField(max_length=50, blank=True)
    auth_code = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='SUCCESS')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'POS Payment Record'
        verbose_name_plural = 'POS Payment Records'

    def __str__(self):
        return f"{self.payment_method}: {self.amount} ({self.status})"


class POSCashTransaction(models.Model):
    TXN_TYPES = [
        ('CASH_IN', 'Cash In / Add Float'),
        ('CASH_OUT', 'Cash Out / Expense / Payout'),
        ('SAFE_DROP', 'Safe Drop / Bank Transfer'),
        ('PETTY_EXPENSE', 'Petty Cash Local Expense'),
    ]

    session = models.ForeignKey(POSSession, on_delete=models.CASCADE, related_name='cash_transactions')
    transaction_type = models.CharField(max_length=20, choices=TXN_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)
    authorized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='authorized_pos_cash_txns')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'POS Cash Transaction'
        verbose_name_plural = 'POS Cash Transactions'

    def __str__(self):
        return f"{self.transaction_type}: {self.amount} - {self.reason}"

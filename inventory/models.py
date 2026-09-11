from django.db import models
from django.conf import settings

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Product Categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class ProductBrand(models.Model):
    name = models.CharField(max_length=100)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=50) # Pieces, Kilograms, Liters, Meters
    symbol = models.CharField(max_length=10) # pcs, kg, ltr, m

    class Meta:
        verbose_name_plural = 'Units of Measure'

    def __str__(self):
        return f"{self.name} ({self.symbol})"

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products')
    brand = models.ForeignKey(ProductBrand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name='products')
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reorder_level = models.PositiveIntegerField(default=10)
    reorder_quantity = models.PositiveIntegerField(default=50)
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_serialized = models.BooleanField(default=False)
    is_batched = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"[{self.sku}] {self.name}"

    @property
    def is_low_stock(self):
        return self.current_stock <= self.reorder_level

    @property
    def total_inventory_value(self):
        return float(self.current_stock) * float(self.cost_price)

class Batch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=50)
    manufacturing_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('product', 'batch_number')
        verbose_name_plural = 'Batches'

    def __str__(self):
        return f"{self.product.sku} - Batch #{self.batch_number} (Qty: {self.quantity})"

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('PURCHASE_RECEIPT', 'Goods Receipt (Purchase)'),
        ('SALES_DELIVERY', 'Goods Delivery (Sales)'),
        ('TRANSFER_IN', 'Internal Transfer IN'),
        ('TRANSFER_OUT', 'Internal Transfer OUT'),
        ('ADJUSTMENT_ADD', 'Stock Adjustment (+ Add)'),
        ('ADJUSTMENT_SUB', 'Stock Adjustment (- Deduct)'),
        ('MFG_ISSUE', 'Manufacturing Material Issue'),
        ('MFG_RECEIPT', 'Manufacturing Finished Goods Receipt'),
        ('RETURN_IN', 'Customer Sales Return'),
        ('RETURN_OUT', 'Supplier Purchase Return'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='stock_movements')
    movement_type = models.CharField(max_length=30, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reference_number = models.CharField(max_length=100, blank=True, null=True) # PO-101, SO-204, etc.
    warehouse_name = models.CharField(max_length=100, default='Main Warehouse')
    notes = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M')} | {self.get_movement_type_display()} | {self.product.sku} | Qty: {self.quantity} | Bal: {self.balance_after}"

class StockAdjustment(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('APPROVED', 'Approved & Applied'),
        ('CANCELLED', 'Cancelled'),
    ]

    adjustment_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    reason = models.CharField(max_length=200) # Annual physical count, damaged goods, shrinkage
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.adjustment_number} - {self.reason} ({self.status})"

class StockAdjustmentItem(models.Model):
    adjustment = models.ForeignKey(StockAdjustment, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    system_stock = models.DecimalField(max_digits=12, decimal_places=2)
    counted_stock = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def difference(self):
        return self.counted_stock - self.system_stock

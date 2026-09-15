from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from organizations.models import Organization
from purchasing.models import Supplier, PurchaseOrder, GoodsReceiptNote
from inventory.models import Product

class VendorPortalProfile(models.Model):
    COMPLIANCE_CHOICES = [
        ('COMPLIANT', 'Fully Compliant (ISO / SOC2)'),
        ('CONDITIONAL', 'Conditional Approval'),
        ('AUDIT_REQUIRED', 'Audit Required'),
        ('SUSPENDED', 'Temporarily Suspended'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='vendor_profiles')
    supplier = models.OneToOneField(Supplier, on_delete=models.CASCADE, related_name='portal_profile')
    vendor_code = models.CharField(max_length=50, unique=True)
    rating_score = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('4.50'))
    compliance_status = models.CharField(max_length=20, choices=COMPLIANCE_CHOICES, default='COMPLIANT')
    bank_swift_code = models.CharField(max_length=50, blank=True)
    bank_iban = models.CharField(max_length=50, blank=True)
    tax_id_number = models.CharField(max_length=100, blank=True)
    portal_access_enabled = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.supplier.name} ({self.vendor_code})"


class SupplierBidRfq(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open for Bidding'),
        ('CLOSED', 'Bidding Closed'),
        ('EVALUATING', 'Evaluating Bids'),
        ('AWARDED', 'Awarded to Supplier'),
        ('CANCELLED', 'Cancelled'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='supplier_rfqs')
    rfq_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_delivery_date = models.DateField()
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rfq_number} - {self.title}"


class SupplierBidRfqItem(models.Model):
    rfq = models.ForeignKey(SupplierBidRfq, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='rfq_items')
    target_quantity = models.PositiveIntegerField()
    target_unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} (Target Qty: {self.target_quantity})"


class SupplierBidSubmission(models.Model):
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('SHORTLISTED', 'Shortlisted'),
        ('AWARDED', 'Awarded'),
        ('REJECTED', 'Rejected'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='bid_submissions')
    rfq = models.ForeignKey(SupplierBidRfq, on_delete=models.CASCADE, related_name='submissions')
    vendor = models.ForeignKey(VendorPortalProfile, on_delete=models.CASCADE, related_name='bids')
    total_bid_amount = models.DecimalField(max_digits=14, decimal_places=2)
    lead_time_days = models.PositiveIntegerField(default=7)
    warranty_months = models.PositiveIntegerField(default=12)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    composite_evaluation_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    vendor_remarks = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-composite_evaluation_score', 'total_bid_amount']

    def __str__(self):
        return f"Bid by {self.vendor.supplier.name} for {self.rfq.rfq_number} (${self.total_bid_amount})"


class AdvanceShippingNotice(models.Model):
    STATUS_CHOICES = [
        ('DISPATCHED', 'Dispatched from Supplier Dock'),
        ('IN_TRANSIT', 'In Transit / Freight Line'),
        ('DELIVERED', 'Delivered at Nexora Facility'),
        ('VERIFIED', 'Verified & Received into Inventory'),
        ('EXCEPTION', 'Logistics Exception / Delayed'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='asns')
    vendor = models.ForeignKey(VendorPortalProfile, on_delete=models.CASCADE, related_name='asns')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='asns')
    asn_number = models.CharField(max_length=50, unique=True)
    carrier_name = models.CharField(max_length=100)
    tracking_number = models.CharField(max_length=100)
    dispatch_date = models.DateField(default=timezone.now)
    estimated_arrival_date = models.DateField()
    package_count = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DISPATCHED')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"ASN {self.asn_number} (PO: {self.purchase_order.po_number})"


class VendorInvoiceUpload(models.Model):
    MATCH_CHOICES = [
        ('PENDING_MATCH', 'Pending 3-Way Match'),
        ('MATCH_PASSED', '3-Way Match Passed (100% Verified)'),
        ('MATCH_FAILED', 'Match Discrepancy Flagged'),
        ('APPROVED', 'Approved for Payment Batch'),
        ('PAID', 'Settled & Paid'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='uploaded_invoices')
    vendor = models.ForeignKey(VendorPortalProfile, on_delete=models.CASCADE, related_name='invoices')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='supplier_invoices')
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField(default=timezone.now)
    subtotal_amount = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    pdf_document_url = models.CharField(max_length=255, blank=True)
    match_status = models.CharField(max_length=20, choices=MATCH_CHOICES, default='PENDING_MATCH')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Inv #{self.invoice_number} by {self.vendor.supplier.name} (${self.total_amount})"


class ThreeWayMatchVerification(models.Model):
    STATUS_CHOICES = [
        ('FULL_MATCH', 'Full 3-Way Match (Zero Discrepancy)'),
        ('PRICE_VARIANCE', 'Price Variance Flagged'),
        ('QUANTITY_VARIANCE', 'Quantity Variance Flagged'),
        ('DISCREPANCY_FLAGGED', 'Critical Discrepancy Flagged'),
        ('OVERRIDDEN_BY_MANAGER', 'Manually Approved & Overridden'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='match_verifications')
    vendor_invoice = models.OneToOneField(VendorInvoiceUpload, on_delete=models.CASCADE, related_name='three_way_match')
    po_amount = models.DecimalField(max_digits=14, decimal_places=2)
    grn_received_amount = models.DecimalField(max_digits=14, decimal_places=2)
    invoice_amount = models.DecimalField(max_digits=14, decimal_places=2)
    price_variance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    quantity_variance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    match_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='FULL_MATCH')
    verified_at = models.DateTimeField(auto_now_add=True)
    auditor_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Match for Inv #{self.vendor_invoice.invoice_number} - {self.match_status}"

from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid


class TaxJurisdiction(models.Model):
    COUNTRY_CHOICES = [
        ('IN', 'India (GST / TCS / TDS)'),
        ('US', 'United States (State & Local Sales Tax)'),
        ('EU', 'European Union (VAT / OSS / VIES)'),
        ('UK', 'United Kingdom (HMRC Making Tax Digital)'),
        ('AE', 'United Arab Emirates (FTA VAT 5%)'),
        ('SG', 'Singapore (IRAS GST 9%)'),
        ('AU', 'Australia (ATO GST 10%)'),
        ('CA', 'Canada (GST / HST / PST / QST)'),
        ('GLOBAL', 'Global / Generic Jurisdiction'),
    ]

    FILING_FREQUENCY = [
        ('MONTHLY', 'Monthly Filing'),
        ('QUARTERLY', 'Quarterly Filing'),
        ('ANNUAL', 'Annual Filing'),
    ]

    country = models.CharField(max_length=10, choices=COUNTRY_CHOICES, default='IN')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    tax_authority_name = models.CharField(max_length=200, default='Central Tax Authority')
    filing_frequency = models.CharField(max_length=20, choices=FILING_FREQUENCY, default='MONTHLY')
    currency = models.CharField(max_length=10, default='USD')
    is_default = models.BooleanField(default=False)
    e_invoicing_mandatory = models.BooleanField(default=False)
    e_way_bill_mandatory = models.BooleanField(default=False)
    e_way_bill_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50000.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['country', 'name']
        verbose_name = 'Tax Jurisdiction'
        verbose_name_plural = 'Tax Jurisdictions'

    def __str__(self):
        return f"{self.get_country_display()} - {self.name} ({self.code})"


class HSNSACCode(models.Model):
    CODE_TYPES = [
        ('HSN', 'HSN (Harmonized System of Nomenclature - Goods)'),
        ('SAC', 'SAC (Services Accounting Code - Services)'),
    ]

    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    code_type = models.CharField(max_length=10, choices=CODE_TYPES, default='HSN')
    standard_gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'), help_text="Total GST % (e.g. 5, 12, 18, 28)")
    is_exempt = models.BooleanField(default=False)
    is_nil_rated = models.BooleanField(default=False)
    rcm_applicable = models.BooleanField(default=False, help_text="Reverse Charge Mechanism Applicable")

    class Meta:
        ordering = ['code']
        verbose_name = 'HSN / SAC Master'
        verbose_name_plural = 'HSN / SAC Masters'

    def __str__(self):
        return f"{self.code} - {self.description[:40]} ({self.standard_gst_rate}%)"


class GSTTaxRate(models.Model):
    jurisdiction = models.ForeignKey(TaxJurisdiction, on_delete=models.CASCADE, related_name='gst_rates')
    name = models.CharField(max_length=100)
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('9.00'), help_text="Central GST %")
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('9.00'), help_text="State / UT GST %")
    igst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'), help_text="Integrated GST %")
    cess_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Compensation Cess %")
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-effective_from']
        verbose_name = 'GST Tax Slab'
        verbose_name_plural = 'GST Tax Slabs'

    def __str__(self):
        return f"{self.name} [IGST: {self.igst_rate}% / CGST+SGST: {self.cgst_rate}+{self.sgst_rate}%]"


class EWayBillRecord(models.Model):
    STATUS_CHOICES = [
        ('GENERATED', 'Generated & Active'),
        ('IN_TRANSIT', 'Goods In-Transit'),
        ('DELIVERED', 'Delivered & Closed'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Validity Expired'),
    ]

    TRANSPORT_MODES = [
        ('ROAD', 'Road Freight'),
        ('RAIL', 'Railways'),
        ('AIR', 'Air Cargo'),
        ('SHIP', 'Sea / Ocean Vessel'),
    ]

    ewb_number = models.CharField(max_length=50, unique=True)
    document_number = models.CharField(max_length=64, help_text="Invoice or Delivery Challan Number")
    document_type = models.CharField(max_length=20, default='TAX_INVOICE')
    transport_mode = models.CharField(max_length=10, choices=TRANSPORT_MODES, default='ROAD')
    vehicle_number = models.CharField(max_length=50, blank=True)
    transporter_id = models.CharField(max_length=50, blank=True, help_text="GSTIN of Transporter")
    transporter_name = models.CharField(max_length=150, blank=True)
    distance_km = models.PositiveIntegerField(default=100)
    from_pincode = models.CharField(max_length=20)
    to_pincode = models.CharField(max_length=20)
    total_invoice_value = models.DecimalField(max_digits=14, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='GENERATED')
    cancel_reason = models.TextField(blank=True)
    payload_json = models.JSONField(default=dict, blank=True)
    response_json = models.JSONField(default=dict, blank=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'e-Way Bill Record'
        verbose_name_plural = 'e-Way Bill Records'

    def __str__(self):
        return f"EWB #{self.ewb_number} ({self.document_number}) - {self.status}"


class EInvoiceIRN(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active / Valid IRN'),
        ('CANCELLED', 'Cancelled with IRP'),
    ]

    irn_hash = models.CharField(max_length=64, unique=True, help_text="64-Character SHA-256 Invoice Reference Number")
    ack_number = models.CharField(max_length=50, unique=True)
    ack_date = models.DateTimeField()
    invoice_number = models.CharField(max_length=64)
    invoice_date = models.DateField()
    seller_gstin = models.CharField(max_length=20)
    buyer_gstin = models.CharField(max_length=20, blank=True)
    total_taxable_value = models.DecimalField(max_digits=14, decimal_places=2)
    total_tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_invoice_value = models.DecimalField(max_digits=14, decimal_places=2)
    qr_code_payload = models.TextField(help_text="Signed QR String Data from Government IRP")
    signed_invoice_jwt = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'e-Invoice IRN'
        verbose_name_plural = 'e-Invoice IRNs'

    def __str__(self):
        return f"IRN: {self.irn_hash[:12]}... ({self.invoice_number})"


class EUVATRule(models.Model):
    member_state_code = models.CharField(max_length=5, unique=True, help_text="e.g. DE, FR, IT, ES, NL")
    country_name = models.CharField(max_length=100)
    standard_vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'))
    reduced_vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))
    super_reduced_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    oss_scheme_enabled = models.BooleanField(default=True, help_text="One-Stop-Shop EU Cross-Border B2C")
    reverse_charge_b2b = models.BooleanField(default=True)
    vies_validation_required = models.BooleanField(default=True)

    class Meta:
        ordering = ['country_name']
        verbose_name = 'EU VAT Rule (OSS/VIES)'
        verbose_name_plural = 'EU VAT Rules (OSS/VIES)'

    def __str__(self):
        return f"{self.country_name} ({self.member_state_code}) - {self.standard_vat_rate}% Standard VAT"


class USStateNexusRate(models.Model):
    state_code = models.CharField(max_length=5, unique=True, help_text="e.g. CA, NY, TX, FL, WA")
    state_name = models.CharField(max_length=100)
    state_sales_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('6.00'))
    avg_local_sales_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.50'))
    economic_nexus_revenue_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100000.00'), help_text="e.g. $100,000 threshold")
    economic_nexus_txn_threshold = models.PositiveIntegerField(default=200, help_text="e.g. 200 transactions")
    has_physical_nexus = models.BooleanField(default=False)
    has_economic_nexus = models.BooleanField(default=False)
    is_origin_based_tax = models.BooleanField(default=False, help_text="True for origin-based states (TX, OH, etc.), False for destination-based")

    class Meta:
        ordering = ['state_name']
        verbose_name = 'US State Tax & Economic Nexus'
        verbose_name_plural = 'US State Taxes & Economic Nexus'

    def __str__(self):
        return f"{self.state_name} ({self.state_code}) - Base: {self.state_sales_tax_rate}%"


class TaxFilingReturn(models.Model):
    RETURN_TYPES = [
        ('GSTR_1', 'GSTR-1 Outward Supplies (India)'),
        ('GSTR_3B', 'GSTR-3B Summary Return & ITC (India)'),
        ('GSTR_9', 'GSTR-9 Annual GST Audit Return (India)'),
        ('EU_OSS_VAT', 'EU One-Stop-Shop VAT Return'),
        ('UK_MTD_VAT', 'UK HMRC MTD VAT Return'),
        ('US_SALES_TAX', 'US State Sales & Use Tax Return'),
        ('FORM_1099_MISC', 'US IRS Form 1099-MISC'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Draft Summary'),
        ('VALIDATED', 'Validated by Engine'),
        ('FILED', 'Filed with Government Portal'),
        ('ACCEPTED', 'Accepted by Tax Department'),
        ('REJECTED', 'Rejected / Requires Amendment'),
    ]

    jurisdiction = models.ForeignKey(TaxJurisdiction, on_delete=models.CASCADE, related_name='tax_filings')
    return_type = models.CharField(max_length=30, choices=RETURN_TYPES)
    period_start = models.DateField()
    period_end = models.DateField()
    total_taxable_turnover = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))
    total_tax_collected = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_itc_claimed = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'), help_text="Input Tax Credit")
    net_tax_payable = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    government_arn_reference = models.CharField(max_length=100, blank=True, help_text="Acknowledgement Reference Number")
    filed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    filed_at = models.DateTimeField(null=True, blank=True)
    summary_metrics_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_end', '-created_at']
        verbose_name = 'Tax Filing & Statutory Return'
        verbose_name_plural = 'Tax Filings & Statutory Returns'

    def __str__(self):
        return f"{self.get_return_type_display()} ({self.period_start} to {self.period_end}) - {self.status}"

from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid


class ShippingCarrier(models.Model):
    CARRIER_TYPES = [
        ('ROAD', 'Road Freight Carrier (FTL / LTL)'),
        ('AIR', 'Airlines & Air Cargo (IATA)'),
        ('OCEAN', 'Ocean Container Shipping Line'),
        ('RAIL', 'Railways Intermodal'),
        ('MULTIMODAL', 'Multimodal 3PL Integrator'),
    ]

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True, help_text="e.g. FEDEX, DHL, MAERSK, MSC, CMA-CGM")
    carrier_type = models.CharField(max_length=20, choices=CARRIER_TYPES, default='ROAD')
    contact_person = models.CharField(max_length=150, blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    contact_email = models.EmailField(blank=True)
    tracking_url_template = models.CharField(max_length=255, blank=True, help_text="Template URL with {tracking_number} placeholder")
    account_number = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Shipping Carrier'
        verbose_name_plural = 'Shipping Carriers'

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.get_carrier_type_display()}"


class FreightRateMatrix(models.Model):
    TRANSPORT_MODES = [
        ('AIR', 'Air Cargo Express (IATA Factor 5000)'),
        ('OCEAN_FCL', 'Ocean Full Container Load (FCL)'),
        ('OCEAN_LCL', 'Ocean Less than Container Load (LCL)'),
        ('ROAD_FTL', 'Road Full Truckload (FTL)'),
        ('ROAD_LTL', 'Road Less than Truckload (LTL)'),
    ]

    carrier = models.ForeignKey(ShippingCarrier, on_delete=models.CASCADE, related_name='rate_cards')
    origin_country = models.CharField(max_length=100, default='United States')
    origin_zone = models.CharField(max_length=100, help_text="e.g. US-EAST, JFK, SHANGHAI")
    destination_country = models.CharField(max_length=100, default='Germany')
    destination_zone = models.CharField(max_length=100, help_text="e.g. EU-CENTRAL, FRA, ROTTERDAM")
    transport_mode = models.CharField(max_length=20, choices=TRANSPORT_MODES, default='AIR')
    rate_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('4.50'))
    minimum_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('75.00'))
    fuel_surcharge_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('12.50'))
    security_surcharge_per_kg = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.15'))
    transit_days_min = models.PositiveIntegerField(default=2)
    transit_days_max = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['carrier', 'origin_zone', 'destination_zone']
        verbose_name = 'Freight Rate Matrix'
        verbose_name_plural = 'Freight Rate Matrices'

    def __str__(self):
        return f"{self.carrier.code}: {self.origin_zone} &rarr; {self.destination_zone} (${self.rate_per_kg}/kg)"


class FreightConsignment(models.Model):
    TRANSPORT_MODES = [
        ('AIR_FREIGHT', 'Air Waybill (AWB)'),
        ('OCEAN_FCL', 'Ocean Bill of Lading (BOL - FCL)'),
        ('OCEAN_LCL', 'Ocean Bill of Lading (BOL - LCL)'),
        ('ROAD_FTL', 'Road Consignment (FTL)'),
        ('ROAD_LTL', 'Road Consignment (LTL)'),
    ]

    STATUS_CHOICES = [
        ('BOOKED', 'Booking Confirmed / Manifest Created'),
        ('PICKED_UP', 'Cargo Picked Up from Shipper'),
        ('AT_TERMINAL', 'Received at Gateway Terminal'),
        ('IN_CUSTOMS', 'Customs Clearance In-Progress'),
        ('IN_TRANSIT', 'In-Transit / Linehaul Flight / Voyage'),
        ('OUT_FOR_DELIVERY', 'Out for Final Mile Delivery'),
        ('DELIVERED', 'Delivered & POD Signed'),
        ('EXCEPTION', 'Exception / Delay / Customs Hold'),
    ]

    INCOTERMS = [
        ('EXW', 'EXW - Ex Works'),
        ('FOB', 'FOB - Free on Board'),
        ('CIF', 'CIF - Cost, Insurance and Freight'),
        ('DDP', 'DDP - Delivered Duty Paid'),
        ('DAP', 'DAP - Delivered at Place'),
        ('CFR', 'CFR - Cost and Freight'),
    ]

    tracking_number = models.CharField(max_length=64, unique=True, default=uuid.uuid4, help_text="Master Air Waybill (MAWB) or Bill of Lading #")
    carrier = models.ForeignKey(ShippingCarrier, on_delete=models.PROTECT, related_name='consignments')
    customer = models.ForeignKey('sales.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='freight_consignments')
    transport_mode = models.CharField(max_length=20, choices=TRANSPORT_MODES, default='AIR_FREIGHT')
    incoterms = models.CharField(max_length=10, choices=INCOTERMS, default='FOB')

    # Shipper / Consignor Details
    shipper_name = models.CharField(max_length=200)
    shipper_address = models.TextField()
    shipper_city = models.CharField(max_length=100)
    shipper_country = models.CharField(max_length=100, default='United States')

    # Consignee / Receiver Details
    consignee_name = models.CharField(max_length=200)
    consignee_address = models.TextField()
    consignee_city = models.CharField(max_length=100)
    consignee_country = models.CharField(max_length=100, default='Germany')

    # Port / Gateway
    origin_hub = models.CharField(max_length=100, default='JFK International Airport')
    destination_hub = models.CharField(max_length=100, default='Frankfurt Airport (FRA)')

    # Cargo Metrics
    total_packages_count = models.PositiveIntegerField(default=1)
    actual_gross_weight_kg = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10.00'))
    volumetric_weight_kg = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10.00'))
    chargeable_weight_kg = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10.00'))
    total_volume_cbm = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.060'))
    declared_customs_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('500.00'))

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BOOKED')
    booking_date = models.DateTimeField(auto_now_add=True)
    estimated_departure = models.DateTimeField(null=True, blank=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    actual_delivery_date = models.DateTimeField(null=True, blank=True)
    proof_of_delivery_signature = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-booking_date']
        verbose_name = 'Freight Consignment (AWB/BOL)'
        verbose_name_plural = 'Freight Consignments (AWB/BOL)'

    def __str__(self):
        return f"{self.tracking_number} ({self.get_transport_mode_display()}) - {self.origin_hub} to {self.destination_hub} [{self.status}]"


class FreightConsignmentItem(models.Model):
    PACKAGE_TYPES = [
        ('BOX', 'Standard Carton / Box'),
        ('PALLET', 'Euro / Standard Wooden Pallet'),
        ('CRATE', 'Heavy Wooden Crate'),
        ('DRUM', 'Steel / Plastic Drum'),
        ('CONTAINER_20FT', '20ft Standard Dry Container'),
        ('CONTAINER_40FT', '40ft High Cube Container'),
    ]

    consignment = models.ForeignKey(FreightConsignment, on_delete=models.CASCADE, related_name='packages')
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES, default='BOX')
    package_description = models.CharField(max_length=255, default='Commercial Electronics & Parts')
    length_cm = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('50.00'))
    width_cm = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('40.00'))
    height_cm = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('30.00'))
    gross_weight_kg = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10.00'))
    hs_code = models.CharField(max_length=20, default='8471.30')
    is_hazardous = models.BooleanField(default=False)
    un_number = models.CharField(max_length=10, blank=True, help_text="e.g. UN3481 for Lithium Ion Batteries")

    class Meta:
        verbose_name = 'Consignment Package Item'
        verbose_name_plural = 'Consignment Package Items'

    def __str__(self):
        return f"{self.get_package_type_display()} ({self.length_cm}x{self.width_cm}x{self.height_cm} cm) - {self.gross_weight_kg} kg"


class TransitMilestoneCheckpoint(models.Model):
    consignment = models.ForeignKey(FreightConsignment, on_delete=models.CASCADE, related_name='checkpoints')
    timestamp = models.DateTimeField(default=None, null=True, blank=True)
    location_city = models.CharField(max_length=100)
    facility_name = models.CharField(max_length=150)
    status_title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Transit Milestone Checkpoint'
        verbose_name_plural = 'Transit Milestone Checkpoints'

    def __str__(self):
        return f"{self.consignment.tracking_number} @ {self.location_city}: {self.status_title}"


class FreightShippingInvoice(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    consignment = models.OneToOneField(FreightConsignment, on_delete=models.CASCADE, related_name='freight_invoice')
    base_freight_charge = models.DecimalField(max_digits=12, decimal_places=2)
    fuel_surcharge_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    customs_brokerage_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    origin_handling_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    destination_handling_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    insurance_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default='PENDING', choices=[('PENDING', 'Pending Payment'), ('PAID', 'Settled & Paid')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Freight Shipping Invoice'
        verbose_name_plural = 'Freight Shipping Invoices'

    def __str__(self):
        return f"Freight Inv #{self.invoice_number[:8]} - {self.consignment.tracking_number} (${self.grand_total})"

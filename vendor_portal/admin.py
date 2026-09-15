from django.contrib import admin
from .models import (
    VendorPortalProfile, SupplierBidRfq, SupplierBidRfqItem,
    SupplierBidSubmission, AdvanceShippingNotice,
    VendorInvoiceUpload, ThreeWayMatchVerification
)

class SupplierBidRfqItemInline(admin.TabularInline):
    model = SupplierBidRfqItem
    extra = 1

@admin.register(VendorPortalProfile)
class VendorPortalProfileAdmin(admin.ModelAdmin):
    list_display = ['vendor_code', 'supplier', 'rating_score', 'compliance_status', 'is_approved']
    list_filter = ['compliance_status', 'is_approved']

@admin.register(SupplierBidRfq)
class SupplierBidRfqAdmin(admin.ModelAdmin):
    list_display = ['rfq_number', 'title', 'target_delivery_date', 'deadline', 'status']
    list_filter = ['status']
    inlines = [SupplierBidRfqItemInline]

@admin.register(SupplierBidSubmission)
class SupplierBidSubmissionAdmin(admin.ModelAdmin):
    list_display = ['rfq', 'vendor', 'total_bid_amount', 'lead_time_days', 'composite_evaluation_score', 'status']
    list_filter = ['status']

@admin.register(AdvanceShippingNotice)
class AdvanceShippingNoticeAdmin(admin.ModelAdmin):
    list_display = ['asn_number', 'vendor', 'purchase_order', 'carrier_name', 'tracking_number', 'status']
    list_filter = ['status']

@admin.register(VendorInvoiceUpload)
class VendorInvoiceUploadAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'vendor', 'purchase_order', 'total_amount', 'match_status']
    list_filter = ['match_status']

@admin.register(ThreeWayMatchVerification)
class ThreeWayMatchVerificationAdmin(admin.ModelAdmin):
    list_display = ['vendor_invoice', 'po_amount', 'invoice_amount', 'price_variance', 'match_status']
    list_filter = ['match_status']

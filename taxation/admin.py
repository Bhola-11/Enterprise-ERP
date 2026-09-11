from django.contrib import admin
from .models import (
    TaxJurisdiction, HSNSACCode, GSTTaxRate, EWayBillRecord,
    EInvoiceIRN, EUVATRule, USStateNexusRate, TaxFilingReturn
)


@admin.register(TaxJurisdiction)
class TaxJurisdictionAdmin(admin.ModelAdmin):
    list_display = ['country', 'name', 'code', 'currency', 'filing_frequency', 'is_default', 'e_invoicing_mandatory', 'e_way_bill_mandatory']
    list_filter = ['country', 'filing_frequency', 'is_default']
    search_fields = ['name', 'code']


@admin.register(HSNSACCode)
class HSNSACCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'code_type', 'standard_gst_rate', 'is_exempt', 'rcm_applicable']
    list_filter = ['code_type', 'is_exempt', 'rcm_applicable']
    search_fields = ['code', 'description']


@admin.register(GSTTaxRate)
class GSTTaxRateAdmin(admin.ModelAdmin):
    list_display = ['name', 'jurisdiction', 'cgst_rate', 'sgst_rate', 'igst_rate', 'cess_rate', 'effective_from', 'is_active']
    list_filter = ['jurisdiction', 'is_active']
    search_fields = ['name']


@admin.register(EWayBillRecord)
class EWayBillRecordAdmin(admin.ModelAdmin):
    list_display = ['ewb_number', 'document_number', 'transport_mode', 'vehicle_number', 'total_invoice_value', 'valid_until', 'status']
    list_filter = ['status', 'transport_mode']
    search_fields = ['ewb_number', 'document_number', 'vehicle_number']


@admin.register(EInvoiceIRN)
class EInvoiceIRNAdmin(admin.ModelAdmin):
    list_display = ['irn_hash', 'invoice_number', 'invoice_date', 'seller_gstin', 'total_invoice_value', 'status', 'created_at']
    list_filter = ['status', 'invoice_date']
    search_fields = ['irn_hash', 'invoice_number', 'seller_gstin', 'buyer_gstin']


@admin.register(EUVATRule)
class EUVATRuleAdmin(admin.ModelAdmin):
    list_display = ['country_name', 'member_state_code', 'standard_vat_rate', 'reduced_vat_rate', 'oss_scheme_enabled', 'reverse_charge_b2b']
    list_filter = ['oss_scheme_enabled', 'reverse_charge_b2b']
    search_fields = ['country_name', 'member_state_code']


@admin.register(USStateNexusRate)
class USStateNexusRateAdmin(admin.ModelAdmin):
    list_display = ['state_name', 'state_code', 'state_sales_tax_rate', 'avg_local_sales_tax_rate', 'economic_nexus_revenue_threshold', 'has_physical_nexus', 'has_economic_nexus']
    list_filter = ['has_physical_nexus', 'has_economic_nexus', 'is_origin_based_tax']
    search_fields = ['state_name', 'state_code']


@admin.register(TaxFilingReturn)
class TaxFilingReturnAdmin(admin.ModelAdmin):
    list_display = ['return_type', 'jurisdiction', 'period_start', 'period_end', 'total_taxable_turnover', 'total_tax_collected', 'net_tax_payable', 'status']
    list_filter = ['return_type', 'status', 'jurisdiction']
    search_fields = ['government_arn_reference']

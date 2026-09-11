from django.contrib import admin
from .models import (
    InspectionPlan, InspectionCharacteristic, QualityInspectionTicket,
    InspectionResultMetric, NonConformanceReport, CAPAAction
)

class InspectionCharacteristicInline(admin.TabularInline):
    model = InspectionCharacteristic
    extra = 1

@admin.register(InspectionPlan)
class InspectionPlanAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'sampling_standard', 'is_active')
    list_filter = ('category', 'sampling_standard', 'is_active')
    inlines = [InspectionCharacteristicInline]

class CAPAActionInline(admin.TabularInline):
    model = CAPAAction
    extra = 1

@admin.register(QualityInspectionTicket)
class QualityInspectionTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'plan', 'reference_code', 'lot_size', 'sample_size', 'disposition', 'status', 'inspection_date')
    list_filter = ('disposition', 'status', 'plan__category')

@admin.register(NonConformanceReport)
class NonConformanceReportAdmin(admin.ModelAdmin):
    list_display = ('ncr_number', 'ticket', 'defect_title', 'defect_severity', 'status', 'created_at')
    list_filter = ('defect_severity', 'status')
    inlines = [CAPAActionInline]

from django.contrib import admin
from .models import ShiftTemplate, ShiftRosterAssignment, BiometricPunchLog, AttendanceSummaryPeriod

@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = ('shift_code', 'name', 'start_time', 'end_time', 'is_night_shift', 'hourly_rate_multiplier', 'is_active')
    list_filter = ('is_night_shift', 'is_active')

@admin.register(ShiftRosterAssignment)
class ShiftRosterAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'shift_template', 'status')
    list_filter = ('status', 'shift_template', 'date')
    search_fields = ('employee__first_name', 'employee__last_name')

@admin.register(BiometricPunchLog)
class BiometricPunchLogAdmin(admin.ModelAdmin):
    list_display = ('employee', 'punch_time', 'punch_type', 'verification_method', 'device_terminal_id')
    list_filter = ('punch_type', 'verification_method')
    search_fields = ('employee__first_name', 'employee__last_name')

@admin.register(AttendanceSummaryPeriod)
class AttendanceSummaryPeriodAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'regular_hours_worked', 'overtime_1_5x_hours', 'overtime_2_0x_hours', 'late_minutes', 'status')
    list_filter = ('status', 'date')

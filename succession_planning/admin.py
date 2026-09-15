from django.contrib import admin
from .models import CriticalRolePosition, TalentProfile, SuccessionPlan

class SuccessionPlanInline(admin.TabularInline):
    model = SuccessionPlan
    extra = 1

@admin.register(CriticalRolePosition)
class CriticalRolePositionAdmin(admin.ModelAdmin):
    list_display = ('position_code', 'title', 'department', 'current_incumbent', 'risk_of_vacancy', 'impact_of_loss', 'target_bench_strength', 'is_active')
    list_filter = ('risk_of_vacancy', 'impact_of_loss', 'department')
    search_fields = ('title', 'position_code')
    inlines = [SuccessionPlanInline]

@admin.register(TalentProfile)
class TalentProfileAdmin(admin.ModelAdmin):
    list_display = ('employee', 'performance_rating', 'potential_rating', 'nine_box_quadrant', 'flight_risk', 'last_calibrated_at')
    list_filter = ('nine_box_quadrant', 'performance_rating', 'potential_rating', 'flight_risk')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')

@admin.register(SuccessionPlan)
class SuccessionPlanAdmin(admin.ModelAdmin):
    list_display = ('critical_position', 'successor_employee', 'readiness_level', 'ranking_priority', 'status')
    list_filter = ('readiness_level', 'status')

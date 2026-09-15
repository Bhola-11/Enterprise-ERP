from django.contrib import admin
from .models import AppraisalCycle, CompetencyFramework, AppraisalSubmission, ContinuousFeedbackNote

class AppraisalSubmissionInline(admin.TabularInline):
    model = AppraisalSubmission
    extra = 0
    fields = ('employee', 'manager', 'self_rating', 'peer_average_rating', 'manager_rating', 'calibrated_final_score', 'overall_band', 'status')

@admin.register(AppraisalCycle)
class AppraisalCycleAdmin(admin.ModelAdmin):
    list_display = ('name', 'cycle_type', 'start_date', 'end_date', 'status', 'is_active')
    list_filter = ('cycle_type', 'status', 'is_active')
    inlines = [AppraisalSubmissionInline]

@admin.register(CompetencyFramework)
class CompetencyFrameworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'weight_percentage', 'is_active')
    list_filter = ('category', 'is_active')

@admin.register(AppraisalSubmission)
class AppraisalSubmissionAdmin(admin.ModelAdmin):
    list_display = ('cycle', 'employee', 'manager', 'calibrated_final_score', 'overall_band', 'status')
    list_filter = ('overall_band', 'status', 'cycle')
    search_fields = ('employee__first_name', 'employee__last_name')

@admin.register(ContinuousFeedbackNote)
class ContinuousFeedbackNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'employee', 'giver', 'feedback_type', 'is_private_manager', 'created_at')
    list_filter = ('feedback_type', 'is_private_manager')

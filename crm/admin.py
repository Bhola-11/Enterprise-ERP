from django.contrib import admin
from .models import Company, Contact, Campaign, Lead, Opportunity, Activity

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'city', 'phone', 'annual_revenue')
    search_fields = ('name', 'industry', 'city')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'company', 'email', 'phone', 'is_primary_contact')
    search_fields = ('first_name', 'last_name', 'email', 'company__name')

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'campaign_type', 'budget', 'expected_revenue', 'start_date', 'is_active')

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'company_name', 'email', 'status', 'lead_score', 'estimated_budget', 'assigned_to')
    list_filter = ('status', 'source')
    search_fields = ('first_name', 'last_name', 'company_name', 'email')

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'stage', 'amount', 'probability', 'expected_close_date', 'assigned_to')
    list_filter = ('stage',)
    search_fields = ('name', 'company__name')

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('subject', 'activity_type', 'due_date', 'is_completed', 'created_by')
    list_filter = ('activity_type', 'is_completed')

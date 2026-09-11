from django.contrib import admin
from .models import TicketCategory, SupportTicket, TicketComment

@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'sla_response_hours', 'sla_resolution_hours')

class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 1

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'subject', 'customer', 'category', 'priority', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority', 'category')
    search_fields = ('ticket_id', 'subject', 'customer__first_name', 'customer__last_name')
    inlines = [TicketCommentInline]

from organizations.models import Organization, FiscalYear
from notifications.models import Notification

def erp_global_context(request):
    org = Organization.objects.first()
    unread_count = 0
    recent_notifications = []

    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        recent_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]

    active_fy = FiscalYear.objects.filter(is_active=True, is_closed=False).first()

    return {
        'company_org': org,
        'company_name': org.name if org else 'Nexora Enterprise OS',
        'currency_symbol': org.currency_symbol if org else '$',
        'currency_code': org.currency if org else 'USD',
        'unread_notifications_count': unread_count,
        'recent_notifications': recent_notifications,
        'active_fiscal_year': active_fy,
        'current_app_version': 'v1.0.0-Enterprise',
    }

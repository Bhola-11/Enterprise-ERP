import json
from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog

class AuditLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._audit_ip = self.get_client_ip(request)
        request._audit_user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

def log_audit_event(user, action, model_name, object_id='', object_repr='', changes=None, request=None, description=''):
    ip = None
    user_agent = None
    if request:
        ip = getattr(request, '_audit_ip', None) or '127.0.0.1'
        user_agent = getattr(request, '_audit_user_agent', None) or ''
    
    return AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        object_repr=str(object_repr)[:255],
        changes=changes or {},
        ip_address=ip,
        user_agent=user_agent,
        description=description
    )

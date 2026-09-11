import hashlib
import secrets
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from .models import APIClient, APIKey, APIGatewayRequestLog, RateLimitPolicy

class APIKeyManager:
    @classmethod
    def generate_api_key(cls, client, name="Standard API Key", key_type='LIVE', expires_in_days=365):
        prefix = "nx_live_" if key_type == 'LIVE' else "nx_test_"
        random_secret = secrets.token_hex(24)
        raw_key = f"{prefix}{random_secret}"

        # Hash key with SHA-256 for secure storage
        key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
        preview = f"{raw_key[:12]}...{raw_key[-6:]}"

        expires_at = timezone.now() + timedelta(days=expires_in_days) if expires_in_days else None

        api_key_obj = APIKey.objects.create(
            client=client,
            key_type=key_type,
            name=name,
            key_prefix=prefix,
            key_hash=key_hash,
            raw_key_preview=preview,
            expires_at=expires_at,
            is_revoked=False
        )
        return api_key_obj, raw_key

    @classmethod
    def verify_key(cls, raw_key):
        if not raw_key:
            return None
        key_hash = hashlib.sha256(raw_key.strip().encode('utf-8')).hexdigest()
        try:
            key_obj = APIKey.objects.select_related('client', 'client__rate_limit_policy').get(key_hash=key_hash)
            if key_obj.is_valid:
                key_obj.total_calls_count += 1
                key_obj.last_used_at = timezone.now()
                key_obj.save(update_fields=['total_calls_count', 'last_used_at'])
                return key_obj
        except APIKey.DoesNotExist:
            return None
        return None

    @classmethod
    def revoke_key(cls, key_id):
        key = APIKey.objects.filter(id=key_id).first()
        if key:
            key.is_revoked = True
            key.save(update_fields=['is_revoked'])
            return True
        return False


class RateLimiterService:
    @classmethod
    def check_rate_limit(cls, api_key_obj, client_ip):
        """
        Sliding rate limiter window per minute.
        Returns (is_allowed: bool, current_rpm: int, max_rpm: int)
        """
        policy = None
        if api_key_obj and api_key_obj.client and api_key_obj.client.rate_limit_policy:
            policy = api_key_obj.client.rate_limit_policy
        else:
            policy = RateLimitPolicy.objects.filter(is_default=True).first()

        max_rpm = policy.requests_per_minute if policy else 120

        # Identifier for rate limit
        identifier = f"ratelimit:{api_key_obj.id if api_key_obj else client_ip}:{timezone.now().strftime('%Y%m%d%H%M')}"
        current_count = cache.get(identifier, 0)

        if current_count >= max_rpm:
            return False, current_count, max_rpm

        cache.set(identifier, current_count + 1, timeout=65)
        return True, current_count + 1, max_rpm


class GatewayTelemetryService:
    @classmethod
    def log_request(cls, api_key, endpoint, method, status_code, response_time_ms, client_ip, user_agent, headers=None, query_params=None):
        client_name = api_key.client.client_name if (api_key and api_key.client) else "Anonymous"
        APIGatewayRequestLog.objects.create(
            api_key=api_key,
            client_name=client_name,
            endpoint=endpoint,
            http_method=method,
            status_code=status_code,
            response_time_ms=Decimal(str(response_time_ms)).quantize(Decimal('0.01')),
            client_ip=client_ip,
            user_agent=user_agent[:255] if user_agent else "",
            request_headers=headers or {},
            query_params=query_params or {}
        )
from typing import Optional, Any
from ..models import ActivityLog
from apps.system.activity_log_types.models import ActivityLogType


def log_activity(
    user,
    action: str,
    log_type_code: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[dict] = None
) -> ActivityLog:
    """Create an activity log"""
    
    # Ensure log type exists
    try:
        log_type = ActivityLogType.objects.get(type_name=log_type_code)
    except ActivityLogType.DoesNotExist:
        
        log_type, _ = ActivityLogType.objects.get_or_create(
            type_name=log_type_code, defaults={'description': 'Auto generated'}
        )
        
    log = ActivityLog.objects.create(
        user=user if user and user.is_authenticated else None,
        log_type=log_type,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {}
    )
    return log

from typing import Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import SystemSetting


import json
from django.core.cache import cache
from apps.system.activity_logs.services.activity_logs import log_activity

@transaction.atomic
def update_setting(
    user,
    setting: SystemSetting,
    value: str,
    description: Optional[str] = None,
    is_public: Optional[bool] = None
) -> SystemSetting:
    """Update a system setting with validation, logging and cache invalidation"""
    
    old_value = setting.setting_value
    
    # 1. Validation
    # Validate value type
    if setting.setting_type == SystemSetting.SettingType.NUMBER:
        try:
            float(value)
        except ValueError:
            raise ValidationError(f"Value for {setting.setting_key} must be a number")
            
    elif setting.setting_type == SystemSetting.SettingType.BOOLEAN:
        if value.lower() not in ['true', 'false', '1', '0']:
            raise ValidationError(f"Value for {setting.setting_key} must be a boolean ('true', 'false', '1', '0')")

    elif setting.setting_type == SystemSetting.SettingType.JSON:
        try:
            json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError(f"Value for {setting.setting_key} must be valid JSON")

    # 2. Update
    setting.setting_value = value
    if description is not None:
        setting.description = description
    if is_public is not None:
        setting.is_public = is_public
        
    setting.updated_by = user
    setting.save()

    # 3. Cache Invalidation
    # Invalidate strict key
    cache.delete(f"system_setting:{setting.setting_key}")
    
    # 4. Audit Logging
    log_activity(
        user=user,
        action="UPDATE",
        log_type_code="SYSTEM_SETTING_UPDATE",
        entity_type="SystemSetting",
        entity_id=setting.id,
        details={
            "key": setting.setting_key,
            "old_value": old_value,
            "new_value": value,
            "changes": "Updated system setting"
        }
    )
    
    return setting

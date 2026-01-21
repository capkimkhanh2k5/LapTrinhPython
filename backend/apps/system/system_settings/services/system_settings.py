from typing import Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import SystemSetting


@transaction.atomic
def update_setting(
    user,
    setting: SystemSetting,
    value: str,
    description: Optional[str] = None,
    is_public: Optional[bool] = None
) -> SystemSetting:
    """Update a system setting"""
    
    # Validate value type if needed
    if setting.setting_type == SystemSetting.SettingType.NUMBER:
        try:
            float(value)
        except ValueError:
            raise ValidationError(f"Value for {setting.setting_key} must be a number")
            
    if setting.setting_type == SystemSetting.SettingType.BOOLEAN:
        if value.lower() not in ['true', 'false', '1', '0']:
            raise ValidationError(f"Value for {setting.setting_key} must be a boolean")

    setting.setting_value = value
    if description is not None:
        setting.description = description
    if is_public is not None:
        setting.is_public = is_public
        
    setting.updated_by = user
    setting.save()
    
    return setting

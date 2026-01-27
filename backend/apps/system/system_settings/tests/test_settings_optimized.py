from django.test import TestCase
from django.core.cache import cache
from django.core.exceptions import ValidationError
from apps.system.system_settings.models import SystemSetting
from apps.system.system_settings.services.system_settings import update_setting
from apps.system.system_settings.selectors.system_settings import get_setting_by_key
from apps.system.activity_logs.models import ActivityLog
from apps.core.users.models import CustomUser

class SystemSettingsOptimizedTest(TestCase):
    def setUp(self):
        cache.clear()
        self.user = CustomUser.objects.create(email='admin@example.com', full_name='Admin User')
        
        # Create initial settings
        self.setting_num = SystemSetting.objects.create(
            setting_key='MAX_UPLOAD_SIZE',
            setting_value='10',
            setting_type=SystemSetting.SettingType.NUMBER,
            updated_by=self.user
        )
        self.setting_bool = SystemSetting.objects.create(
            setting_key='MAINTENANCE_MODE',
            setting_value='false',
            setting_type=SystemSetting.SettingType.BOOLEAN,
            updated_by=self.user
        )
        self.setting_json = SystemSetting.objects.create(
            setting_key='THEME_CONFIG',
            setting_value='{"dark": true}',
            setting_type=SystemSetting.SettingType.JSON,
            updated_by=self.user
        )

    def test_validation(self):
        """Test strict validation logic"""
        # Test Number
        with self.assertRaisesMessage(ValidationError, "must be a number"):
            update_setting(self.user, self.setting_num, "not-a-number")
            
        # Test Boolean
        with self.assertRaisesMessage(ValidationError, "must be a boolean"):
            update_setting(self.user, self.setting_bool, "maybe")
            
        # Test JSON
        with self.assertRaisesMessage(ValidationError, "must be valid JSON"):
            update_setting(self.user, self.setting_json, "{invalid_json}")
            
        # Test Success
        update_setting(self.user, self.setting_num, "20.5") # Should work
        self.assertEqual(self.setting_num.setting_value, "20.5")

    def test_caching_flow(self):
        """Test Read-through Cache and Invalidation"""
        key = self.setting_num.setting_key
        
        # 1. First read (Cache Miss -> Set Cache)
        # Verify cache is empty initially
        self.assertIsNone(cache.get(f"system_setting:{key}"))
        
        obj = get_setting_by_key(key)
        self.assertEqual(obj.setting_value, "10")
        
        # Verify cache is set
        cached_obj = cache.get(f"system_setting:{key}")
        self.assertIsNotNone(cached_obj)
        self.assertEqual(cached_obj.setting_value, "10")
        
        # 2. Update (Should Invalidate Cache)
        update_setting(self.user, self.setting_num, "50")
        
        # Verify cache is deleted
        self.assertIsNone(cache.get(f"system_setting:{key}"))
        
        # 3. Read again (Cache Miss -> Set Cache with New Value)
        obj_new = get_setting_by_key(key)
        self.assertEqual(obj_new.setting_value, "50")
        self.assertEqual(cache.get(f"system_setting:{key}").setting_value, "50")

    def test_audit_logging(self):
        """Test Activity Log creation"""
        update_setting(self.user, self.setting_bool, "true")
        
        # Check logs
        log = ActivityLog.objects.last()
        self.assertIsNotNone(log)
        self.assertEqual(log.action, "UPDATE")
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.details['key'], 'MAINTENANCE_MODE')
        self.assertEqual(log.details['old_value'], 'false')
        self.assertEqual(log.details['new_value'], 'true')

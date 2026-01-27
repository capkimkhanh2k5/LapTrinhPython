from typing import Optional, Iterable
from django.db.models import QuerySet
from django.core.cache import cache

from ..models import SystemSetting


def list_settings(filters: dict = None) -> QuerySet[SystemSetting]:
    """
        Danh sách các setting theo các filter
    """
    queryset = SystemSetting.objects.all()
    
    if filters:
        if filters.get('category'):
            queryset = queryset.filter(category=filters['category'])
        if filters.get('is_public') is not None:
            queryset = queryset.filter(is_public=filters['is_public'])
        if filters.get('search'):
            queryset = queryset.filter(setting_key__icontains=filters['search'])
            
    return queryset.order_by('category', 'setting_key')


def get_setting_by_key(key: str) -> Optional[SystemSetting]:
    """
    Lấy setting theo key (có caching)
    """
    cache_key = f"system_setting:{key}"
    
    # Try getting from cache
    setting_data = cache.get(cache_key)
    if setting_data:
        return setting_data

    try:
        setting = SystemSetting.objects.get(setting_key=key)
        # Cache for 24 hours
        cache.set(cache_key, setting, timeout=86400)
        return setting
    except SystemSetting.DoesNotExist:
        return None

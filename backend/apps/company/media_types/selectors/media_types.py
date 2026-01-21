from typing import Optional
from django.db.models import QuerySet
from ..models import MediaType


def list_media_types(is_active: Optional[bool] = None) -> QuerySet[MediaType]:
    """Lấy danh sách loại media"""
    queryset = MediaType.objects.all().order_by('type_name')
    
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    
    return queryset


def get_media_type_by_id(media_type_id: int) -> Optional[MediaType]:
    """Lấy loại media theo ID"""
    try:
        return MediaType.objects.get(id=media_type_id)
    except MediaType.DoesNotExist:
        return None


def get_media_type_by_name(type_name: str) -> Optional[MediaType]:
    """Lấy loại media theo tên"""
    try:
        return MediaType.objects.get(type_name=type_name)
    except MediaType.DoesNotExist:
        return None

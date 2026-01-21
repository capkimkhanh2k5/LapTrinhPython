from typing import Optional
from pydantic import BaseModel
from ..models import MediaType


class MediaTypeInput(BaseModel):
    """Pydantic model cho input tạo/cập nhật MediaType"""
    type_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


def create_media_type(data: MediaTypeInput) -> MediaType:
    """Tạo loại media mới"""
    # Kiểm tra tên đã tồn tại
    if MediaType.objects.filter(type_name=data.type_name).exists():
        raise ValueError(f"Media type '{data.type_name}' already exists")
    
    media_type = MediaType.objects.create(
        type_name=data.type_name,
        description=data.description or '',
        is_active=data.is_active if data.is_active is not None else True
    )
    
    return media_type


def update_media_type(media_type: MediaType, data: MediaTypeInput) -> MediaType:
    """Cập nhật loại media"""
    if data.type_name is not None:
        # Kiểm tra tên mới không trùng với loại khác
        if (MediaType.objects.filter(type_name=data.type_name)
                .exclude(id=media_type.id).exists()):
            raise ValueError(f"Media type '{data.type_name}' already exists")
        media_type.type_name = data.type_name
    
    if data.description is not None:
        media_type.description = data.description
    
    if data.is_active is not None:
        media_type.is_active = data.is_active
    
    media_type.save()
    return media_type


def delete_media_type(media_type: MediaType) -> None:
    """Xóa loại media"""
    # Kiểm tra có media nào đang sử dụng loại này không
    if hasattr(media_type, 'company_medias') and media_type.company_medias.exists():
        raise ValueError("Cannot delete media type that is in use")
    
    media_type.delete()

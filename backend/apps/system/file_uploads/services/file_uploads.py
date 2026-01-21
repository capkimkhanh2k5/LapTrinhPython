import os
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from ..models import FileUpload


def save_upload(user, file_obj, entity_type=None, entity_id=None, is_public=False) -> FileUpload:
    """
        Lưu file đã tải lên và tạo record
    """
    
    # Tạo tên file duy nhất
    ext = os.path.splitext(file_obj.name)[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    
    # Xác định đường dẫn dựa trên public/private
    sub_folder = 'public' if is_public else 'private'
    file_path = f"uploads/{sub_folder}/{unique_name}"
    
    # Lưu file
    saved_path = default_storage.save(file_path, ContentFile(file_obj.read()))
    
    # Tạo record
    upload = FileUpload.objects.create(
        user=user,
        file_name=unique_name,
        original_name=file_obj.name,
        file_path=saved_path,
        file_type=ext.replace('.', ''),
        file_size=file_obj.size,
        mime_type=file_obj.content_type,
        entity_type=entity_type,
        entity_id=entity_id,
        is_public=is_public
    )
    
    return upload

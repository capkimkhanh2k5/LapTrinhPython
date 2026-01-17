from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
from pydantic import BaseModel, EmailStr
from ..models import CustomUser


class UserCreateInput(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ''
    role: str = 'recruiter'


def create_user(data: UserCreateInput) -> CustomUser:
    """
    Service to create a user with hashed password.
    Tuân thủ N-Tier: Services chứa logic WRITE (create, update, delete)
    """
    with transaction.atomic():
        user = CustomUser.objects.create_user(
            email=data.email,
            password=data.password,
            full_name=data.full_name,
            role=data.role
        )
        return user


class UserUpdateInput(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None

def update_user(user: CustomUser, data: UserUpdateInput) -> CustomUser:
    """
    Cập nhật thông tin cơ bản của user.
    """
    fields_to_update = []
    
    if data.full_name is not None:
        user.full_name = data.full_name
        fields_to_update.append('full_name')
        
    if data.phone is not None:
        user.phone = data.phone
        fields_to_update.append('phone')
        
    if data.avatar_url is not None:
        user.avatar_url = data.avatar_url
        fields_to_update.append('avatar_url')
    
    if fields_to_update:
        user.save(update_fields=fields_to_update)
        
    return user


def delete_user(user: CustomUser) -> None:
    """
    Xóa user (Hard Delete).
    """
    user.delete()


def update_user_status(user: CustomUser, status: str) -> CustomUser:
    """
    Cập nhật trạng thái user (active/banned).
    """
    if status not in CustomUser.Status.values:
        raise ValueError("Trạng thái không hợp lệ")
    
    user.status = status
    if status == CustomUser.Status.BANNED:
        user.is_active = False # Chặn login ngay lập tức
    elif status == CustomUser.Status.ACTIVE:
        user.is_active = True
        
    user.save(update_fields=['status', 'is_active'])
    return user


def update_user_role(user: CustomUser, role: str) -> CustomUser:
    """
    Cập nhật vai trò user (Admin only).
    """
    if role not in CustomUser.Role.values:
        raise ValueError("Vai trò không hợp lệ")
        
    user.role = role
    
    # Cập nhật is_staff/is_superuser nếu cần
    if role == CustomUser.Role.ADMIN:
        user.is_staff = True
        user.is_superuser = True
    else:
        user.is_staff = False
        user.is_superuser = False
        
    user.save(update_fields=['role', 'is_staff', 'is_superuser'])
    return user


def upload_user_avatar(user: CustomUser, file) -> CustomUser:
    """
    Upload avatar cho user.
    Lưu file vào media/avatars/{user_id}/{filename}
    """
    # Tạo đường dẫn file
    file_ext = os.path.splitext(file.name)[1]
    file_path = f"avatars/{user.id}/avatar{file_ext}"
    
    # Xóa file cũ nếu có
    if default_storage.exists(file_path):
        default_storage.delete(file_path)
    
    # Lưu file mới
    saved_path = default_storage.save(file_path, ContentFile(file.read()))
    
    # Cập nhật URL
    file_url = default_storage.url(saved_path)
    
    user.avatar_url = file_url
    user.save(update_fields=['avatar_url'])
    
    return user

def bulk_user_action(ids: list[int], action: str, value: str = None) -> dict:
    """
    Thực hiện hành động hàng loạt trên danh sách user IDs.
    Supported actions: 'delete', 'update_status'
    """
    users = CustomUser.objects.filter(id__in=ids)
    count = users.count()
    
    if action == 'delete':
        users.delete() 
        return {"deleted": count}
        
    elif action == 'update_status':
        if value is None:
            raise ValueError("Cần cung cấp value cho update_status")
        users.update(status=value, is_active=(value == CustomUser.Status.ACTIVE))
        return {"updated": count, "status": value}
        
    else:
        raise ValueError("Hành động không được hỗ trợ")

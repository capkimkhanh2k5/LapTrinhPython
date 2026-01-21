import time
import re

import cloudinary
import cloudinary.uploader

from django.core.files.uploadedfile import UploadedFile


ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']


def validate_image_file(file: UploadedFile, max_size_mb: int = 2) -> None:
    """
    Validate file ảnh
    - Kiểm tra file có được cung cấp
    - Kiểm tra loại file hợp lệ
    - Kiểm tra kích thước file
    """
    if not file:
        raise ValueError("File is not provided")
    
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("File type is not allowed. Only JPEG, PNG, GIF, WEBP are allowed")
    
    if file.size > max_size_mb * 1024 * 1024:
        raise ValueError(f"File size excess max size. MAX {max_size_mb}MB")


def save_company_file(company_id: int, file: UploadedFile, file_type: str, resource_type: str = 'auto') -> str:
    """
    Lưu file vào Cloudinary
    
    Args:
        company_id: ID của company
        file: File upload
        file_type: Loại file (logo, banner, office_photo, ...)
        resource_type: Loại resource ('image', 'video', 'raw', 'auto'). Mặc định là 'auto'.
    
    Returns:
        URL của file đã upload
    """
    public_id = f"companies/{company_id}/{file_type}_{company_id}_{int(time.time())}"
    try: 
        result = cloudinary.uploader.upload(
            file, 
            public_id=public_id, 
            resource_type=resource_type, 
            overwrite=True
        )
        return result['secure_url']
    except Exception as e:
        raise ValueError(f"Upload file thất bại: {str(e)}")


def delete_company_file(file_url: str, resource_type: str = 'image') -> bool:
    """
    Xóa file từ Cloudinary dựa trên URL
    
    Args:
        file_url: URL của file cần xóa
        resource_type: Loại resource ('image', 'video', 'raw')
    
    Returns:
        True nếu xóa thành công, False nếu thất bại
    """
    if not file_url:
        return False
    
    # Extract public_id từ URL
    match = re.search(r'/upload/(?:v\d+/)?(.+)\.[^.]+$', file_url)
    if not match:
        return False
    
    public_id = match.group(1)
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return result.get('result') == 'ok'
    except Exception:
        return False


def save_raw_file(folder: str, file, prefix: str) -> str:
    """
    Upload raw file (PDF, CSV, etc.) lên Cloudinary
    
    Args:
        folder: Thư mục lưu trữ trên Cloudinary (vd: 'referrals/cvs', 'reports')
        file: File upload (UploadedFile hoặc bytes-like object)
        prefix: Tiền tố cho tên file (vd: 'cv', 'report_revenue')
    
    Returns:
        URL của file đã upload
    """
    public_id = f"{folder}/{prefix}_{int(time.time())}"
    try:
        result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            resource_type='raw',
            overwrite=True
        )
        return result['secure_url']
    except Exception as e:
        raise ValueError(f"Upload raw file failed: {str(e)}")


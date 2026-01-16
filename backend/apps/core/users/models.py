from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """Bảng Users - Quản lý tất cả người dùng"""
    
    class Role(models.TextChoices):
        RECRUITER = 'recruiter', _('Ứng viên')
        COMPANY = 'company', _('Công ty')
        ADMIN = 'admin', _('Quản trị viên')
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Hoạt động')
        INACTIVE = 'inactive', _('Không hoạt động')
        BANNED = 'banned', _('Bị khóa')
    
    # Disable username, use email instead
    username = None
    email = models.EmailField(
        unique=True,
        db_index=True,
        verbose_name='Email'
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name='Họ và tên'
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Số điện thoại'
    )
    avatar_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='URL ảnh đại diện'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RECRUITER,
        db_index=True,
        verbose_name='Vai trò'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        verbose_name='Trạng thái'
    )
    email_verified = models.BooleanField(
        default=False,
        verbose_name='Email đã xác minh'
    )
    email_verification_token = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Token xác minh email'
    )
    password_reset_token = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Token reset mật khẩu'
    )
    password_reset_expires = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Hạn reset mật khẩu'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    # Note: last_login is already provided by AbstractUser
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Người dùng'
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
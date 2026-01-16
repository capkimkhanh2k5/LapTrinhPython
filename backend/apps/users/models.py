from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    # Enum role
    class Role(models.TextChoices):
        RECRUITER = 'recruiter', _('Recruiter')
        COMPANY = 'company', _('Company')
        ADMIN = 'admin', _('Admin')
    
    # Enum status
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        BANNED = 'banned', _('Banned')
    
    # Dùng email để đăng nhập
    username = None 
    email = models.EmailField(_('email address'), unique=True)
    
    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.RECRUITER
    )
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.ACTIVE
    )
    email_verified = models.BooleanField(default=False)
    
    # Config
    USERNAME_FIELD = 'email' # Dùng email để đăng nhập
    REQUIRED_FIELDS = []     # Không yêu cầu thêm thông tin (ngoài email/pass)
    
    def __str__(self):
        return f"{self.email} ({self.role})"
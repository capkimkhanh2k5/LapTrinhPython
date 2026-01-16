from django.db import models


class FileUpload(models.Model):
    """Bảng File_Uploads - Quản lý file upload"""
    
    user = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='file_uploads',
        db_index=True,
        verbose_name='Người dùng'
    )
    file_name = models.CharField(
        max_length=255,
        verbose_name='Tên file'
    )
    original_name = models.CharField(
        max_length=255,
        verbose_name='Tên file gốc'
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name='Đường dẫn file'
    )
    file_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Loại file'
    )
    file_size = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Kích thước (bytes)'
    )
    mime_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='MIME type'
    )
    entity_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Loại đối tượng'
    )
    entity_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID đối tượng'
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='Công khai'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'file_uploads'
        verbose_name = 'File upload'
        verbose_name_plural = 'File upload'
        indexes = [
            models.Index(fields=['entity_type', 'entity_id'], name='idx_file_entity'),
        ]
    
    def __str__(self):
        return self.original_name

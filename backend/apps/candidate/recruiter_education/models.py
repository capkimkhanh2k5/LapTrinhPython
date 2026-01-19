from django.db import models


class RecruiterEducation(models.Model):
    """Bảng Recruiter_Education - Học vấn"""
    
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='education',
        db_index=True,
        verbose_name='Recruiter'
    )
    school_name = models.CharField(
        max_length=255,
        verbose_name='School name'
    )
    degree = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Degree'
    )
    field_of_study = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Field of study'
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Start date'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='End date'
    )
    is_current = models.BooleanField(
        default=False,
        verbose_name='Is current'
    )
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='GPA'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Description'
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name='Display order'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at'
    )
    
    class Meta:
        db_table = 'recruiter_education'
        verbose_name = 'Recruiter education'
        verbose_name_plural = 'Recruiter education'
        ordering = ['-start_date', 'display_order']
    
    def __str__(self):
        return f"{self.school_name} - {self.degree}"

from django.db import models


class SkillEndorsement(models.Model):
    """Bảng Skill_Endorsements - Xác nhận kỹ năng"""
    
    recruiter_skill = models.ForeignKey(
        'candidate_recruiter_skills.RecruiterSkill',
        on_delete=models.CASCADE,
        related_name='endorsements',
        db_index=True,
        verbose_name='Kỹ năng ứng viên'
    )
    endorsed_by = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='given_endorsements',
        db_index=True,
        verbose_name='Người xác nhận'
    )
    relationship = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Mối quan hệ'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'skill_endorsements'
        verbose_name = 'Xác nhận kỹ năng'
        verbose_name_plural = 'Xác nhận kỹ năng'
        unique_together = ['recruiter_skill', 'endorsed_by']
    
    def __str__(self):
        return f"{self.endorsed_by.user.full_name} xác nhận {self.recruiter_skill.skill.name}"

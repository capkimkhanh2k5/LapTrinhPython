from rest_framework import serializers
from apps.recruitment.jobs.models import Job

class JobOwnershipValidator:
    """
    Validator to ensure that a list of Job IDs:
    1. Exist
    2. Belong to the authenticated user's company
    3. Are in 'published' status
    """
    requires_context = True

    def __call__(self, value, serializer_field):
        # Kết quả là 1 list IDs
        if not value:
            return

        request = serializer_field.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required to validate job ownership.")

        user = request.user
        
        # Xác định công ty dựa trên vai trò người dùng (giả sử Recruiter/Company user)
        # Lưu ý các kiểm tra có thể cần điều chỉnh nếu quan hệ User <-> Company thay đổi
        company_profile = getattr(user, 'company_profile', None)
        # Hoặc nếu người dùng là nhà tuyển dụng liên kết với một công ty
        recruiter_profile = getattr(user, 'recruiter_profile', None)
        
        company = None
        if company_profile:
            company = company_profile
        elif recruiter_profile:
             company = recruiter_profile.company
        
        if not company:
            # Nếu người dùng không có ngữ cảnh công ty, họ không nên thêm công việc
            raise serializers.ValidationError("User is not associated with any company.")

        # Truy vấn các công việc hợp lệ
        valid_jobs_count = Job.objects.filter(
            id__in=value,
            company=company,
            status=Job.Status.PUBLISHED
        ).count()

        # So sánh số lượng
        # set(value) xử lý các ID trùng lặp trong đầu vào
        if valid_jobs_count != len(set(value)):
            raise serializers.ValidationError(
                "One or more jobs are invalid (not found, not published, or belong to another company)."
            )

import csv

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.recruitment.jobs.selectors.jobs import get_job_by_id
from apps.recruitment.interviews.selectors.interviews import list_interviews_by_application
from apps.recruitment.interviews.serializers import InterviewListSerializer
from apps.recruitment.application_status_history.selectors.application_status_history import list_history_by_application
from apps.recruitment.application_status_history.serializers import StatusHistorySerializer
from apps.recruitment.application_status_history.services.application_status_history import log_status_history
from apps.candidate.recruiters.selectors.recruiters import get_recruiter_by_user

from django.http import HttpResponse

from .models import Application

from .services.applications import (
    applicant_withdraw,
    send_offer,
    change_application_status,
    rate_application,
    withdraw_application,
    update_application,
    create_application,
    ApplicationUpdateInput,
    ApplicationCreateInput,
)

from .serializers import (
    ApplicationWithdrawSerializer,
    ApplicationStatusSerializer,
    ApplicationUpdateSerializer,
    ApplicationCreateSerializer,
    ApplicationOfferSerializer,
    ApplicationListSerializer,
    ApplicationDetailSerializer,
    ApplicationRejectSerializer,
    ApplicationNotesSerializer,
    ApplicationRatingSerializer,
)

from .selectors.applications import (
    list_applications_by_job,
    list_applications_by_status,
    list_applications_by_rating,
    list_applications_for_export,
    get_application_stats,
    get_application_by_id,
    search_applications,
)

class JobApplicationViewSet(viewsets.GenericViewSet):
    """
        ViewSet cho danh sách applications của một job.
        Nested URL: /api/jobs/:job_id/applications/
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        job_id = self.kwargs.get('job_id')
        filters = self._build_filters()
        return list_applications_by_job(job_id, filters)
    
    def _build_filters(self):
        """
            Build filters từ query params
        """
        filters = {}
        params = self.request.query_params
        
        if params.get('status'):
            filters['status'] = params['status']
        
        if params.get('rating'):
            filters['rating'] = int(params['rating'])
        
        return filters
    
    def _get_job_or_404(self, job_id):
        """
            Helper: Lấy job hoặc trả về 404
        """
        job = get_job_by_id(job_id)
        if not job:
            return None, Response(
                {"detail": "Job not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        return job, None
    
    def _check_job_owner(self, request, job):
        """
            Helper: Kiểm tra nếu user sở hữu job
        """
        if job.company.user != request.user:
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        return None
    
    def list(self, request, job_id=None):
        """
            GET /api/jobs/:job_id/applications/
            Danh sách ứng viên cho job
        """
        job, error = self._get_job_or_404(job_id)
        if error:
            return error
        
        permission_error = self._check_job_owner(request, job)
        if permission_error:
            return permission_error
        
        queryset = self.get_queryset()
        serializer = ApplicationListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def _filter_by_status(self, request, job_id, filter_status):
        """
            Helper: Filter applications by status
        """
        
        job, error = self._get_job_or_404(job_id)
        if error:
            return error
        
        permission_error = self._check_job_owner(request, job)
        if permission_error:
            return permission_error
        
        queryset = list_applications_by_status(job_id, filter_status)
        serializer = ApplicationListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def pending(self, request, job_id=None):
        """
            GET /api/jobs/:job_id/applications/pending/
            Danh sách đơn chờ xử lý
        """
        return self._filter_by_status(request, job_id, 'pending')
    
    def shortlisted(self, request, job_id=None):
        """
            GET /api/jobs/:job_id/applications/shortlisted/
            Danh sách đơn đã chọn
        """
        return self._filter_by_status(request, job_id, 'shortlisted')
    
    def rejected(self, request, job_id=None):
        """
            GET /api/jobs/:job_id/applications/rejected/
            Danh sách đơn bị từ chối
        """
        return self._filter_by_status(request, job_id, 'rejected')
    
    def by_rating(self, request, job_id=None):
        """
            GET /api/jobs/:job_id/applications/by-rating/
            Lọc theo điểm đánh giá
        """
        
        job, error = self._get_job_or_404(job_id)
        if error:
            return error
        
        permission_error = self._check_job_owner(request, job)
        if permission_error:
            return permission_error
        
        # Parse query params
        rating = request.query_params.get('rating')
        min_rating = request.query_params.get('min_rating')
        max_rating = request.query_params.get('max_rating')
        
        queryset = list_applications_by_rating(
            job_id,
            rating=int(rating) if rating else None,
            min_rating=int(min_rating) if min_rating else None,
            max_rating=int(max_rating) if max_rating else None
        )
        serializer = ApplicationListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def search(self, request, job_id=None):
        """
            GET /api/jobs/:job_id/applications/search/
            Tìm kiếm trong đơn ứng tuyển
        """
        
        job, error = self._get_job_or_404(job_id)
        if error:
            return error
        
        permission_error = self._check_job_owner(request, job)
        if permission_error:
            return permission_error
        
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
        
        queryset = search_applications(job_id, query)
        serializer = ApplicationListSerializer(queryset, many=True)
        return Response(serializer.data)


class ApplicationViewSet(viewsets.GenericViewSet):
    """
        ViewSet cho quản lý applications.
        URL: /api/applications/
    """
    permission_classes = [IsAuthenticated]
    
    def _is_applicant(self, request, application):
        """
            Kiểm tra nếu user là người nộp đơn
        """
        return application.recruiter.user == request.user
    
    def _is_job_owner(self, request, application):
        """
            Kiểm tra nếu user là người sở hữu job
        """
        return application.job.company.user == request.user
    
    def _get_application_or_404(self, pk):
        """
            Lấy application hoặc trả về 404
        """

        application = get_application_by_id(pk)
        if not application:
            return None, Response(
                {"detail": "Application not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        return application, None
    
    def create(self, request):
        """
            POST /api/applications/
            Nộp đơn ứng tuyển
        """
        
        recruiter = get_recruiter_by_user(request.user)
        if not recruiter:
            return Response(
                {"detail": "Recruiter profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = ApplicationCreateInput(**serializer.validated_data)
            application = create_application(recruiter, input_data)
            return Response(
                ApplicationDetailSerializer(application).data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        """
            GET /api/applications/:id/
            Chi tiết đơn ứng tuyển
        """
        application, error = self._get_application_or_404(pk)
        if error:
            return error
        
        # Both applicant and job owner can view
        if not self._is_applicant(request, application) and not self._is_job_owner(request, application):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response(ApplicationDetailSerializer(application).data)
    
    def update(self, request, pk=None):
        """
            PUT /api/applications/:id/
            Cập nhật đơn (chỉ applicant)
        """
        
        application, error = self._get_application_or_404(pk)
        if error:
            return error
        
        if not self._is_applicant(request, application):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ApplicationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = ApplicationUpdateInput(**serializer.validated_data)
            updated = update_application(application, input_data)
            return Response(ApplicationDetailSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """
            DELETE /api/applications/:id/
            Rút đơn (chỉ applicant)
        """
        
        application, error = self._get_application_or_404(pk)
        if error:
            return error
        
        if not self._is_applicant(request, application):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            withdraw_application(application)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def change_status(self, request, pk=None):
        """
            PATCH /api/applications/:id/status/
            Đổi trạng thái (chỉ job owner)
        """
        
        application, error = self._get_application_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, application):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ApplicationStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated = change_application_status(
                application,
                serializer.validated_data['status'],
                request.user,
                serializer.validated_data.get('notes')
            )
            return Response(ApplicationDetailSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def rate(self, request, pk=None):
        """
            PATCH /api/applications/:id/rating/
            Đánh giá ứng viên (chỉ job owner)
        """
        
        application, error = self._get_application_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, application):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ApplicationRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated = rate_application(
                application,
                serializer.validated_data['rating'],
                serializer.validated_data.get('notes')
            )
            return Response(ApplicationDetailSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def add_notes(self, request, pk=None):
        """
            POST /api/applications/:id/notes/
            Thêm ghi chú (chỉ job owner)
        """

        application, error = self._get_application_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, application):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ApplicationNotesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update notes
        application.notes = serializer.validated_data['notes']
        application.save()
        
        # Log to history
        log_status_history(
            application,
            application.status,
            application.status,  # same status
            request.user,
            f"Ghi chú: {serializer.validated_data['notes']}"
        )
        
        return Response(ApplicationDetailSerializer(application).data)
    
    def history(self, request, pk=None):
        """
            GET /api/applications/:id/history/
            Lịch sử thay đổi trạng thái (cả applicant và job owner)
        """
        
        application, error = self._get_application_or_404(pk)
        if error:
            return error
        
        # Both can view history
        if not self._is_applicant(request, application) and not self._is_job_owner(request, application):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        history = list_history_by_application(int(pk))
        serializer = StatusHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    def shortlist(self, request, pk=None):
        """
            POST /api/applications/:id/shortlist/
            Thêm vào danh sách rút gọn (chỉ job owner)
        """
        
        application, error = self._get_application_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, application):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            old_status = application.status
            updated = change_application_status(
                application,
                'shortlisted',
                request.user,
                request.data.get('notes')
            )
            
            # Log history
            log_status_history(
                application,
                old_status,
                'shortlisted',
                request.user,
                request.data.get('notes')
            )
            
            return Response(ApplicationDetailSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def reject(self, request, pk=None):
        """
            POST /api/applications/:id/reject/
            Từ chối ứng viên (chỉ job owner)
        """
        
        application, error = self._get_application_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, application):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ApplicationRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reason = serializer.validated_data.get('reason', 'Không phù hợp')
        
        try:
            old_status = application.status
            updated = change_application_status(
                application,
                'rejected',
                request.user,
                reason
            )
            
            # Log history
            log_status_history(
                application,
                old_status,
                'rejected',
                request.user,
                reason
            )
            
            return Response(ApplicationDetailSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def offer(self, request, pk=None):
        """
            POST /api/applications/:id/offer/
            Gửi offer (chỉ job owner)
        """
        
        application, error = self._get_application_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, application):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ApplicationOfferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            old_status = application.status
            updated = send_offer(
                application,
                serializer.validated_data['offer_details'],
                request.user,
                serializer.validated_data.get('salary'),
                serializer.validated_data.get('start_date')
            )
            
            # Log history
            log_status_history(
                application,
                old_status,
                'offered',
                request.user,
                f"Offer: {serializer.validated_data['offer_details']}"
            )
            
            return Response(ApplicationDetailSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def applicant_withdraw(self, request, pk=None):
        """
            POST /api/applications/:id/withdraw/
            Ứng viên rút đơn (chỉ applicant)
        """
        
        application, error = self._get_application_or_404(pk)
        if error:
            return error
        
        if not self._is_applicant(request, application):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ApplicationWithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated = applicant_withdraw(
                application,
                serializer.validated_data.get('reason')
            )
            return Response(ApplicationDetailSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def stats(self, request):
        """
            GET /api/applications/stats/
            Thống kê đơn ứng tuyển
        """
        
        stats = get_application_stats(request.user)
        return Response(stats)
    
    def bulk_action_view(self, request):
        """
            POST /api/applications/bulk-action/
            Thao tác hàng loạt
        """
        from .serializers import ApplicationBulkActionSerializer
        from .services.applications import bulk_action
        
        serializer = ApplicationBulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = bulk_action(
                serializer.validated_data['application_ids'],
                serializer.validated_data['action'],
                request.user,
                serializer.validated_data.get('notes')
            )
            return Response(result)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def export(self, request):
        """
            GET /api/applications/export/
            Export danh sách applications (CSV)
        """
        
        job_id = request.query_params.get('job_id')
        status_filter = request.query_params.get('status')
        
        applications = list_applications_for_export(
            request.user,
            job_id=int(job_id) if job_id else None,
            status=status_filter
        )
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="applications.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Job Title', 'Applicant Name', 'Email', 
            'Status', 'Rating', 'Applied At', 'Notes'
        ])
        
        for app in applications:
            writer.writerow([
                app.id,
                app.job.title,
                app.recruiter.user.full_name,
                app.recruiter.user.email,
                app.status,
                app.rating or '',
                app.applied_at.strftime('%Y-%m-%d %H:%M'),
                app.notes or ''
            ])
        
        return response
    
    def list_interviews(self, request, pk=None):
        """
            GET /api/applications/:id/interviews/
            Lịch sử phỏng vấn của đơn
        """
        
        application, error = self._get_application_or_404(pk)
        if error:
            return error
        
        # Both job owner and applicant can view
        if not self._is_job_owner(request, application) and not self._is_applicant(request, application):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        interviews = list_interviews_by_application(int(pk))
        return Response(InterviewListSerializer(interviews, many=True).data)

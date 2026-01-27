from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from datetime import datetime

from .models import Interview
from apps.recruitment.applications.models import Application

from .serializers import (
    InterviewListSerializer, InterviewDetailSerializer,
    InterviewCreateSerializer, InterviewUpdateSerializer,
    InterviewRescheduleSerializer, InterviewCancelSerializer
)
from apps.recruitment.interview_interviewers.services.interview_interviewers import (
    save_interviewer_feedback,
    add_interviewer,
    remove_interviewer,
)
from apps.recruitment.interview_interviewers.serializers import (
    InterviewerFeedbackSerializer,
    InterviewerListSerializer,
    InterviewerAddSerializer,
)
from apps.recruitment.interview_interviewers.selectors.interview_interviewers import (
    get_interviewer,
    list_interviewers,
)

from .services.interviews import (
    send_reminder,
    add_feedback,
    complete_interview,
    cancel_interview,
    reschedule_interview,
    delete_interview,
    update_interview,
    create_interview,
    InterviewUpdateInput,
    InterviewCreateInput,
)

from .selectors.interviews import (
    get_upcoming_interviews,
    get_calendar_interviews,
)
from .serializers import (
    InterviewReminderSerializer,
    InterviewFeedbackSerializer,
    InterviewCompleteSerializer,
)


class InterviewViewSet(viewsets.GenericViewSet):
    """
        ViewSet cho quản lý interviews.
        URL: /api/interviews/
    """
    permission_classes = [IsAuthenticated]
    
    def _is_job_owner(self, request, interview):
        """
            Kiểm tra nếu user sở hữu job
        """
        return interview.application.job.company.user == request.user
    
    def _is_applicant(self, request, interview):
        """
            Kiểm tra nếu user là người ứng tuyển
        """
        return interview.application.recruiter.user == request.user
    
    def _get_interview_or_404(self, pk):
        """
            Lấy interview hoặc trả về 404
        """
        from .selectors.interviews import get_interview_by_id
        interview = get_interview_by_id(pk)
        if not interview:
            return None, Response(
                {"detail": "Interview not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        return interview, None
    
    def create(self, request):
        """
            POST /api/interviews/
            Tạo lịch phỏng vấn
        """
        serializer = InterviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            application = Application.objects.select_related(
                'job__company'
            ).get(id=serializer.validated_data['application_id'])
        except Application.DoesNotExist:
            return Response(
                {"detail": "Application not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if application.job.company.user != request.user:
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            input_data = InterviewCreateInput(**serializer.validated_data)
            interview = create_interview(input_data, request.user)
            return Response(
                InterviewDetailSerializer(interview).data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        """
            GET /api/interviews/:id/
            Chi tiết lịch phỏng vấn
        """
        interview, error = self._get_interview_or_404(pk)
        if error:
            return error
        
        # Cả owner và applicant có quyền xem
        if not self._is_job_owner(request, interview) and not self._is_applicant(request, interview):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response(InterviewDetailSerializer(interview).data)
    
    def update(self, request, pk=None):
        """
            PUT /api/interviews/:id/
            Cập nhật lịch phỏng vấn
        """
        
        interview, error = self._get_interview_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, interview):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = InterviewUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = InterviewUpdateInput(**serializer.validated_data)
            updated = update_interview(interview, input_data)
            return Response(InterviewDetailSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """
            DELETE /api/interviews/:id/
            Xóa lịch phỏng vấn
        """
        
        interview, error = self._get_interview_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, interview):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            delete_interview(interview)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def reschedule(self, request, pk=None):
        """
            PATCH /api/interviews/:id/reschedule/
            Đổi lịch phỏng vấn
        """
        
        interview, error = self._get_interview_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, interview):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = InterviewRescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated = reschedule_interview(
                interview,
                serializer.validated_data['scheduled_at'],
                serializer.validated_data.get('reason')
            )
            return Response(InterviewDetailSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def cancel(self, request, pk=None):
        """
            PATCH /api/interviews/:id/cancel/
            Hủy lịch phỏng vấn
        """
        
        interview, error = self._get_interview_or_404(pk)
        if error:
            return error
        
        # Cả owner và applicant có quyền hủy
        if not self._is_job_owner(request, interview) and not self._is_applicant(request, interview):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = InterviewCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated = cancel_interview(
                interview,
                serializer.validated_data.get('reason')
            )
            return Response(InterviewDetailSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def complete(self, request, pk=None):
        """
            PATCH /api/interviews/:id/complete/
            Hoàn thành phỏng vấn
        """
        
        interview, error = self._get_interview_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, interview):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = InterviewCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated = complete_interview(
                interview,
                serializer.validated_data['result'],
                serializer.validated_data.get('feedback')
            )
            return Response(InterviewDetailSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def add_feedback(self, request, pk=None):
        """
            POST /api/interviews/:id/feedback/
            Thêm feedback
        """
        
        interview, error = self._get_interview_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, interview):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = InterviewFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated = add_feedback(interview, serializer.validated_data['feedback'])
        return Response(InterviewDetailSerializer(updated).data)
    
    def send_reminder_action(self, request, pk=None):
        """
            POST /api/interviews/:id/send-reminder/
            Gửi nhắc nhở
        """
        
        interview, error = self._get_interview_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, interview):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = InterviewReminderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = send_reminder(interview, serializer.validated_data.get('message'))
            return Response(result)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def calendar(self, request):
        """
            GET /api/interviews/calendar/
            Calendar view
        """
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"detail": "start_date & end_date is required!"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Format date must be YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        calendar_data = get_calendar_interviews(request.user, start, end)
        return Response(calendar_data)
    
    def upcoming(self, request):
        """
            GET /api/interviews/upcoming/
            Danh sách phỏng vấn sắp tới
        """
        
        days = request.query_params.get('days', 7)
        try:
            days = int(days)
        except ValueError:
            days = 7
        
        interviews = get_upcoming_interviews(request.user, days)
        return Response(InterviewListSerializer(interviews, many=True).data)
    
    def list_interviewers(self, request, pk=None):
        """
            GET /api/interviews/:id/interviewers/
            Danh sách người phỏng vấn
        """
        
        interview, error = self._get_interview_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, interview):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        interviewers = list_interviewers(int(pk))
        return Response(InterviewerListSerializer(interviewers, many=True).data)
    
    def add_interviewer(self, request, pk=None):
        """
            POST /api/interviews/:id/interviewers/
            Thêm người phỏng vấn
        """
        
        interview, error = self._get_interview_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, interview):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = InterviewerAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            interviewer = add_interviewer(
                interview,
                serializer.validated_data['user_id'],
                serializer.validated_data.get('role')
            )
            return Response(
                InterviewerListSerializer(interviewer).data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def remove_interviewer(self, request, pk=None, user_id=None):
        """
            DELETE /api/interviews/:id/interviewers/:userId/
            Xóa người phỏng vấn
        """

        interview, error = self._get_interview_or_404(pk)
        if error:
            return error
        
        if not self._is_job_owner(request, interview):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            remove_interviewer(interview, user_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def interviewer_feedback(self, request, pk=None, user_id=None):
        """
            POST /api/interviews/:id/interviewers/:userId/feedback/
            Feedback của interviewer
        """

        interview, error = self._get_interview_or_404(pk)
        if error:
            return error
        
        # Check permission - người phỏng vấn có thể thêm feedback cho mình
        interviewer_record = get_interviewer(int(pk), user_id)
        if not interviewer_record:
            return Response(
                {"detail": "Interviewer not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        is_owner = self._is_job_owner(request, interview)
        is_the_interviewer = (interviewer_record.interviewer_id == request.user.id)
        
        if not is_owner and not is_the_interviewer:
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = InterviewerFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated = save_interviewer_feedback(
                interview,
                user_id,
                serializer.validated_data.get('feedback'),
                serializer.validated_data.get('rating')
            )
            return Response(InterviewerListSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

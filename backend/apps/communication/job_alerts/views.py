from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count

from .models import JobAlert, JobAlertMatch
from .serializers import JobAlertSerializer, JobAlertMatchSerializer
from apps.communication.job_alerts.services.matching import JobMatchingService
# from apps.recruitment.jobs.models import Job # Needed if testing against random job or recently created? Using matching service instead.

class JobAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet cho Job Alerts.
    - CRUD JobAlerts
    - Toggle status
    - Test matching
    - View matched jobs
    """
    serializer_class = JobAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Lấy recruiter profile của user
        if not hasattr(self.request.user, 'recruiter_profile'):
            return JobAlert.objects.none()
        return JobAlert.objects.filter(recruiter=self.request.user.recruiter_profile)
    
    def perform_create(self, serializer):
        # Auto assign recruiter
        if not hasattr(self.request.user, 'recruiter_profile'):
            raise serializers.ValidationError("User must be a Candidate/Recruiter to create alerts.")
        serializer.save(recruiter=self.request.user.recruiter_profile)

    @action(detail=True, methods=['patch'])
    def toggle(self, request, pk=None):
        """Bật/tắt job alert"""
        alert = self.get_object()
        alert.is_active = not alert.is_active
        alert.save()
        return Response({'status': 'success', 'is_active': alert.is_active})

    @action(detail=True, methods=['get'], url_path='matched-jobs')
    def matched_jobs(self, request, pk=None):
        """Lấy danh sách các jobs đã được hệ thống match trước đó"""
        alert = self.get_object()
        matches = JobAlertMatch.objects.filter(job_alert=alert).select_related('job', 'job__company')
        
        page = self.paginate_queryset(matches)
        if page is not None:
            serializer = JobAlertMatchSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = JobAlertMatchSerializer(matches, many=True)
        return Response(serializer.data)

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema

from .models import ActivityLog
from .serializers import ActivityLogSerializer
from .selectors.activity_logs import list_activity_logs


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing Activity Logs"""
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return list_activity_logs(filters=self.request.query_params.dict())
    
    @extend_schema(summary="List system activity logs")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
        
    @extend_schema(summary="Get activity log details")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

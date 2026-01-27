from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from django.utils import timezone
from .services.notifications import bulk_mark_as_read
import json
import time

from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationMarkReadSerializer,
    NotificationSettingSerializer,
)
from .selectors.notifications import (
    list_notifications,
    list_unread_notifications,
    get_notification_by_id,
    count_unread_notifications,
)
from .services.notifications import (
    mark_as_read,
    mark_all_as_read,
    delete_notification,
    clear_all_notifications,
)


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for managing user notifications.
    
    Endpoints:
    - GET    /api/notifications/           - List all notifications
    - GET    /api/notifications/unread/    - List unread notifications
    - GET    /api/notifications/:id/       - Get notification detail
    - PATCH  /api/notifications/:id/read/  - Mark as read
    - PATCH  /api/notifications/read-all/  - Mark all as read
    - DELETE /api/notifications/:id/       - Delete notification
    - DELETE /api/notifications/clear-all/ - Delete all notifications
    - GET    /api/notifications/settings/  - Get notification settings
    - GET    /api/notifications/stream/    - SSE stream for real-time
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """Get queryset filtered by current user."""
        return list_notifications(self.request.user.id)
    
    def list(self, request):
        """
        GET /api/notifications/
        
        List all notifications for the current user.
        Supports filtering by is_read and notification_type_id.
        """
        is_read = request.query_params.get('is_read')
        notification_type_id = request.query_params.get('notification_type_id')
        
        # Convert is_read string to boolean
        is_read_filter = None
        if is_read is not None:
            is_read_filter = is_read.lower() in ('true', '1', 'yes')
        
        # Convert notification_type_id to int
        type_filter = None
        if notification_type_id:
            try:
                type_filter = int(notification_type_id)
            except ValueError:
                pass
        
        queryset = list_notifications(
            user_id=request.user.id,
            is_read=is_read_filter,
            notification_type_id=type_filter
        )
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NotificationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = NotificationSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='unread')
    def unread(self, request):
        """
        GET /api/notifications/unread/
        
        List unread notifications for the current user.
        """
        queryset = list_unread_notifications(request.user.id)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NotificationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = NotificationSerializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })
    
    def retrieve(self, request, pk=None):
        """
        GET /api/notifications/:id/
        
        Get notification detail.
        """
        notification = get_notification_by_id(pk)
        
        if not notification:
            return Response(
                {'detail': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if notification.user_id != request.user.id:
            return Response(
                {'detail': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], url_path='read')
    def mark_read(self, request, pk=None):
        """
        PATCH /api/notifications/:id/read/
        
        Mark a notification as read.
        """
        try:
            notification = mark_as_read(
                notification_id=pk,
                user_id=request.user.id
            )
            serializer = NotificationSerializer(notification)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['patch'], url_path='mark-read')
    def bulk_mark_read(self, request):
        """
        PATCH /api/notifications/mark-read/
        
        Mark multiple or all notifications as read.
        Body: {"ids": [1,2], "read_all": false}
        """
        
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        read_all = serializer.validated_data.get('read_all', False)
        notification_ids = serializer.validated_data.get('notification_ids', [])
        
        if read_all:
            updated_count = mark_all_as_read(request.user.id)
            message = 'All notifications marked as read'
        else:
            updated_count = bulk_mark_as_read(
                notification_ids=notification_ids,
                user_id=request.user.id
            )
            message = f'{updated_count} notifications marked as read'
            
        return Response({
            'detail': message,
            'updated_count': updated_count
        })

    @action(detail=False, methods=['patch'], url_path='read-all')
    def mark_all_read(self, request):
        """
        PATCH /api/notifications/read-all/
        Kept for backward compatibility.
        """
        updated_count = mark_all_as_read(request.user.id)
        return Response({
            'detail': 'All notifications marked as read',
            'updated_count': updated_count
        })
    
    def destroy(self, request, pk=None):
        """
        DELETE /api/notifications/:id/
        
        Delete a notification.
        """
        try:
            delete_notification(
                notification_id=pk,
                user_id=request.user.id
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['delete'], url_path='clear-all')
    def clear_all(self, request):
        """
        DELETE /api/notifications/clear-all/
        
        Delete all notifications for the current user.
        """
        deleted_count = clear_all_notifications(request.user.id)
        return Response({
            'detail': 'All notifications deleted',
            'deleted_count': deleted_count
        })
    
    @action(detail=False, methods=['get'], url_path='settings')
    def notification_settings(self, request):
        """
        GET /api/notifications/settings/
        
        Get notification settings for the current user.
        Note: This is a placeholder - actual settings would come from
        a NotificationSetting model linked to the user.
        """
        # Default settings - in real implementation, fetch from database
        settings_data = {
            'email_notifications': True,
            'push_notifications': True,
            'job_alerts': True,
            'application_updates': True,
            'message_notifications': True,
        }
        
        serializer = NotificationSettingSerializer(settings_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='count')
    def count(self, request):
        """
        GET /api/notifications/count/
        
        Get count of unread notifications.
        """
        unread_count = count_unread_notifications(request.user.id)
        return Response({
            'unread_count': unread_count
        })
    
    @action(detail=False, methods=['get'], url_path='stream')
    def stream(self, request):
        """
        GET /api/notifications/stream/
        
        SSE (Server-Sent Events) stream for real-time notifications.
        Client should connect to this endpoint and listen for events.
        """
        def event_stream():
            """Generator function for SSE."""
            last_check = None
            
            while True:
                # Get new notifications
                queryset = list_unread_notifications(request.user.id)
                
                if last_check:
                    queryset = queryset.filter(created_at__gt=last_check)
                
                if queryset.exists():
                    for notification in queryset:
                        data = {
                            'id': notification.id,
                            'title': notification.title,
                            'content': notification.content,
                            'notification_type': notification.notification_type.type_name,
                            'created_at': notification.created_at.isoformat(),
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                
                last_check = timezone.now()
                
                # Send heartbeat every 30 seconds
                yield f": heartbeat\n\n"
                time.sleep(5)  # Check every 5 seconds
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

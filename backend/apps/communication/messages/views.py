from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import (
    MessageSerializer,
    AttachmentUploadSerializer,
)
from .selectors.messages import (
    count_unread_messages,
)
from .services.messages import (
    delete_message,
    upload_attachment,
)


class MessageViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing individual messages.
    
    Endpoints:
    - DELETE /api/messages/:id/              - Delete message
    - GET    /api/messages/unread-count/     - Get unread count
    - POST   /api/messages/upload-attachment/ - Upload attachment
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    
    def destroy(self, request, pk=None):
        """
        DELETE /api/messages/:id/
        
        Delete a message (only your own messages).
        """
        try:
            delete_message(message_id=pk, user_id=request.user.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """
        GET /api/messages/unread-count/
        
        Get total unread message count for the current user.
        """
        count = count_unread_messages(request.user.id)
        return Response({
            'unread_count': count
        })
    
    @action(
        detail=False,
        methods=['post'],
        url_path='upload-attachment',
        parser_classes=[MultiPartParser, FormParser]
    )
    def upload_attachment_action(self, request):
        """
        POST /api/messages/upload-attachment/
        
        Upload a file attachment.
        Returns the URL of the uploaded file.
        """
        serializer = AttachmentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        file = serializer.validated_data['file']
        
        try:
            url = upload_attachment(file=file, user=request.user)
            return Response({
                'url': url,
                'filename': file.name,
                'size': file.size
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'detail': f'Failed to upload file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

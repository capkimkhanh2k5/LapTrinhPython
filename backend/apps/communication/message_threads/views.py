# MessageThread ViewSet
# REST API endpoints for message threads

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import MessageThread
from .serializers import (
    MessageThreadSerializer,
    MessageThreadDetailSerializer,
    MessageThreadCreateSerializer,
    AddParticipantSerializer,
)
from apps.communication.messages.serializers import (
    MessageSerializer,
    MessageCreateSerializer,
    MongoMessageSerializer,
)
from apps.communication.messages.selectors.messages import (
    list_threads,
    get_thread_by_id,
    list_messages,
)
from apps.communication.messages.services.messages import (
    create_thread,
    delete_thread,
    send_message,
    mark_thread_as_read,
    add_participant,
    remove_participant,
    ThreadCreateInput,
    MessageCreateInput,
)

class MessageThreadViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for managing message threads.
    
    Endpoints:
    - GET    /api/messages/threads/                      - List all threads
    - POST   /api/messages/threads/                      - Create new thread
    - GET    /api/messages/threads/:id/                  - Get thread detail
    - DELETE /api/messages/threads/:id/                  - Leave/delete thread
    - GET    /api/messages/threads/:id/messages/         - Get messages in thread
    - POST   /api/messages/threads/:id/messages/         - Send message
    - PATCH  /api/messages/threads/:id/read/             - Mark thread as read
    - POST   /api/messages/threads/:id/participants/     - Add participant
    - DELETE /api/messages/threads/:id/participants/:uid/ - Remove participant
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = MessageThreadSerializer
    
    def get_queryset(self):
        """Get queryset filtered by current user."""
        return list_threads(self.request.user.id)
    
    def list(self, request):
        """
        GET /api/messages/threads/
        
        List all message threads for the current user.
        """
        queryset = self.get_queryset()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MessageThreadSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageThreadSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    def create(self, request):
        """
        POST /api/messages/threads/
        
        Create a new message thread.
        """
        serializer = MessageThreadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            thread = create_thread(
                creator=request.user,
                data=ThreadCreateInput(**serializer.validated_data)
            )
            response_serializer = MessageThreadDetailSerializer(thread)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def retrieve(self, request, pk=None):
        """
        GET /api/messages/threads/:id/
        
        Get thread detail.
        """
        thread = get_thread_by_id(pk, request.user.id)
        
        if not thread:
            return Response(
                {'detail': 'Thread not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MessageThreadDetailSerializer(thread)
        return Response(serializer.data)
    
    def destroy(self, request, pk=None):
        """
        DELETE /api/messages/threads/:id/
        
        Leave/delete a thread.
        """
        try:
            delete_thread(thread_id=pk, user_id=request.user.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        """
        GET  /api/messages/threads/:id/messages/ - Get messages in thread
        POST /api/messages/threads/:id/messages/ - Send message to thread
        """
        if request.method == 'GET':
            return self._list_messages(request, pk)
        else:
            return self._send_message(request, pk)
    
    def _list_messages(self, request, thread_id):
        """Get messages in a thread."""
        messages = list_messages(thread_id, request.user.id)
        
        if messages is None:
            return Response(
                {'detail': 'Thread not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MongoMessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MongoMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    def _send_message(self, request, thread_id):
        """Send a message to a thread."""
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            message = send_message(
                thread_id=thread_id,
                sender=request.user,
                data=MessageCreateInput(**serializer.validated_data)
            )
            response_serializer = MessageSerializer(message)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['patch'], url_path='read')
    def mark_read(self, request, pk=None):
        """
        PATCH /api/messages/threads/:id/read/
        
        Mark thread as read.
        """
        try:
            mark_thread_as_read(thread_id=pk, user_id=request.user.id)
            return Response({'detail': 'Thread marked as read'})
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], url_path='participants')
    def add_participant_action(self, request, pk=None):
        """
        POST /api/messages/threads/:id/participants/
        
        Add a participant to the thread.
        """
        serializer = AddParticipantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            participant = add_participant(
                thread_id=pk,
                user_id=serializer.validated_data['user_id'],
                adder_id=request.user.id
            )
            return Response({
                'detail': 'Participant added successfully',
                'participant_id': participant.id
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(
        detail=True,
        methods=['delete'],
        url_path='participants/(?P<user_id>[0-9]+)'
    )
    def remove_participant_action(self, request, pk=None, user_id=None):
        """
        DELETE /api/messages/threads/:id/participants/:user_id/
        
        Remove a participant from the thread.
        """
        try:
            remove_participant(
                thread_id=pk,
                user_id=int(user_id),
                remover_id=request.user.id
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

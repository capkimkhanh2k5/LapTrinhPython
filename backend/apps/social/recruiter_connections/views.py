from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.social.recruiter_connections.models import RecruiterConnection
from apps.social.recruiter_connections.serializers import (
    ConnectionRequestSerializer,
    ConnectionListSerializer,
    ConnectionDetailSerializer,
    SuggestionSerializer,
)
from apps.social.recruiter_connections.services.recruiter_connections import (
    SendConnectionInput,
    send_connection_request,
    accept_connection,
    reject_connection,
    delete_connection,
    get_connection_suggestions,
)
from apps.social.recruiter_connections.selectors.recruiter_connections import (
    get_recruiter_connections,
    get_connection_by_id,
    get_pending_connections,
    get_connection_count,
)
from apps.candidate.recruiters.models import Recruiter


class ConnectionViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Connection operations.
    
    Endpoints:
    - DELETE /api/connections/:id/ - Delete connection
    - GET /api/connections/pending/ - Get pending requests
    - GET /api/connections/suggestions/ - Get suggestions
    - PATCH /api/connections/:id/accept/ - Accept connection
    - PATCH /api/connections/:id/reject/ - Reject connection
    """
    permission_classes = [IsAuthenticated]
    
    def destroy(self, request, pk=None):
        """DELETE /api/connections/:id - Delete a connection."""
        try:
            delete_connection(pk, request.user.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except RecruiterConnection.DoesNotExist:
            return Response(
                {'error': 'Connection not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """GET /api/connections/pending - Get pending connection requests."""
        try:
            recruiter = Recruiter.objects.get(user=request.user)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'User is not a recruiter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        received = get_pending_connections(recruiter.id)
        serializer = ConnectionListSerializer(received, many=True)
        
        return Response({
            'pending_requests': serializer.data,
            'total': received.count(),
        })
    
    @action(detail=False, methods=['get'], url_path='suggestions')
    def suggestions(self, request):
        """GET /api/connections/suggestions - Get connection suggestions."""
        try:
            recruiter = Recruiter.objects.get(user=request.user)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'User is not a recruiter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        limit = int(request.query_params.get('limit', 10))
        suggestions = get_connection_suggestions(recruiter.id, limit=limit)
        
        serializer = SuggestionSerializer(suggestions, many=True)
        
        return Response({
            'suggestions': serializer.data,
            'total': len(suggestions),
        })
    
    @action(detail=True, methods=['patch'], url_path='accept')
    def accept(self, request, pk=None):
        """PATCH /api/connections/:id/accept - Accept a connection request."""
        try:
            connection = accept_connection(pk, request.user.id)
            serializer = ConnectionDetailSerializer(connection)
            return Response(serializer.data)
        except RecruiterConnection.DoesNotExist:
            return Response(
                {'error': 'Connection not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['patch'], url_path='reject')
    def reject(self, request, pk=None):
        """PATCH /api/connections/:id/reject - Reject a connection request."""
        try:
            connection = reject_connection(pk, request.user.id)
            serializer = ConnectionDetailSerializer(connection)
            return Response(serializer.data)
        except RecruiterConnection.DoesNotExist:
            return Response(
                {'error': 'Connection not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RecruiterConnectionsView(viewsets.GenericViewSet):
    """
    Nested ViewSet for Recruiter Connections.
    
    GET /api/recruiters/:id/connections - List connections
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request, recruiter_id=None):
        """Get all connections for a recruiter."""
        try:
            recruiter = Recruiter.objects.get(id=recruiter_id)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'Recruiter not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only owner can see connections
        if recruiter.user != request.user:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        status_filter = request.query_params.get('status', 'accepted')
        connections = get_recruiter_connections(recruiter_id, status=status_filter)
        counts = get_connection_count(recruiter_id)
        
        serializer = ConnectionListSerializer(connections, many=True)
        
        return Response({
            'recruiter_id': recruiter_id,
            'connections': serializer.data,
            'counts': counts,
        })


class SendConnectionView(viewsets.GenericViewSet):
    """
    POST /api/recruiters/:id/connect - Send connection request
    """
    permission_classes = [IsAuthenticated]
    
    def create(self, request, recruiter_id=None):
        """Send a connection request."""
        try:
            requester = Recruiter.objects.get(user=request.user)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'User is not a recruiter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ConnectionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            input_data = SendConnectionInput(
                requester_id=requester.id,
                receiver_id=recruiter_id,
                message=serializer.validated_data.get('message')
            )
            connection = send_connection_request(input_data)
            
            response_serializer = ConnectionDetailSerializer(connection)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'Recruiter not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

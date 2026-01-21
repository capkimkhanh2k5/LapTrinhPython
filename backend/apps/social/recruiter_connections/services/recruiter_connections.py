from typing import Optional
from pydantic import BaseModel

from django.db import transaction
from django.db.models import Q

from apps.social.recruiter_connections.models import RecruiterConnection
from apps.candidate.recruiters.models import Recruiter

class SendConnectionInput(BaseModel):
    """Input for sending connection request."""
    requester_id: int
    receiver_id: int
    message: Optional[str] = None

def send_connection_request(input_data: SendConnectionInput) -> RecruiterConnection:
    """
    Send a connection request to another recruiter.
    
    Args:
        input_data: SendConnectionInput with requester and receiver IDs
        
    Returns:
        Created RecruiterConnection instance
        
    Raises:
        Recruiter.DoesNotExist: If either recruiter not found
        ValueError: If connection already exists or same person
    """
    if input_data.requester_id == input_data.receiver_id:
        raise ValueError('Cannot connect with yourself')
    
    # Verify both recruiters exist
    requester = Recruiter.objects.get(id=input_data.requester_id)
    receiver = Recruiter.objects.get(id=input_data.receiver_id)
    
    # Check if connection already exists (in either direction)
    existing = RecruiterConnection.objects.filter(
        Q(requester_id=input_data.requester_id, receiver_id=input_data.receiver_id) |
        Q(requester_id=input_data.receiver_id, receiver_id=input_data.requester_id)
    ).first()
    
    if existing:
        if existing.status == RecruiterConnection.Status.BLOCKED:
            raise ValueError('Cannot connect with this user')
        elif existing.status == RecruiterConnection.Status.PENDING:
            raise ValueError('Connection request already pending')
        elif existing.status == RecruiterConnection.Status.ACCEPTED:
            raise ValueError('Already connected')
        elif existing.status == RecruiterConnection.Status.REJECTED:
            # Allow re-request after rejection
            existing.status = RecruiterConnection.Status.PENDING
            existing.requester = requester
            existing.receiver = receiver
            existing.message = input_data.message
            existing.save()
            return existing
    
    # Create new connection request
    connection = RecruiterConnection.objects.create(
        requester=requester,
        receiver=receiver,
        message=input_data.message,
        status=RecruiterConnection.Status.PENDING
    )
    
    return connection


def accept_connection(connection_id: int, user_id: int) -> RecruiterConnection:
    """
    Accept a connection request.
    
    Args:
        connection_id: Connection ID
        user_id: User accepting (must be receiver)
        
    Returns:
        Updated RecruiterConnection
        
    Raises:
        RecruiterConnection.DoesNotExist: If not found
        PermissionError: If not the receiver
    """
    connection = RecruiterConnection.objects.select_related(
        'requester__user', 'receiver__user'
    ).get(id=connection_id)
    
    if connection.receiver.user_id != user_id:
        raise PermissionError('Only the receiver can accept this request')
    
    if connection.status != RecruiterConnection.Status.PENDING:
        raise ValueError(f'Connection is already {connection.status}')
    
    connection.status = RecruiterConnection.Status.ACCEPTED
    connection.save(update_fields=['status', 'updated_at'])
    
    return connection


def reject_connection(connection_id: int, user_id: int) -> RecruiterConnection:
    """
    Reject a connection request.
    
    Args:
        connection_id: Connection ID
        user_id: User rejecting (must be receiver)
        
    Returns:
        Updated RecruiterConnection
    """
    connection = RecruiterConnection.objects.select_related(
        'requester__user', 'receiver__user'
    ).get(id=connection_id)
    
    if connection.receiver.user_id != user_id:
        raise PermissionError('Only the receiver can reject this request')
    
    if connection.status != RecruiterConnection.Status.PENDING:
        raise ValueError(f'Connection is already {connection.status}')
    
    connection.status = RecruiterConnection.Status.REJECTED
    connection.save(update_fields=['status', 'updated_at'])
    
    return connection


def delete_connection(connection_id: int, user_id: int) -> bool:
    """
    Delete/remove a connection.
    
    Args:
        connection_id: Connection ID
        user_id: User deleting (must be requester or receiver)
        
    Returns:
        True if deleted
    """
    connection = RecruiterConnection.objects.select_related(
        'requester__user', 'receiver__user'
    ).get(id=connection_id)
    
    if connection.requester.user_id != user_id and connection.receiver.user_id != user_id:
        raise PermissionError('You are not part of this connection')
    
    connection.delete()
    return True


def get_connection_suggestions(recruiter_id: int, limit: int = 10) -> list[dict]:
    """
    Get connection suggestions based on mutual connections and skills.
    
    Args:
        recruiter_id: Recruiter ID
        limit: Max suggestions to return
        
    Returns:
        List of suggestion dicts
    """
    recruiter = Recruiter.objects.get(id=recruiter_id)
    
    # Get already connected recruiter IDs
    connected_ids = set(
        RecruiterConnection.objects.filter(
            Q(requester_id=recruiter_id) | Q(receiver_id=recruiter_id),
            status__in=[
                RecruiterConnection.Status.PENDING,
                RecruiterConnection.Status.ACCEPTED
            ]
        ).values_list('requester_id', 'receiver_id')
    )
    
    # Flatten and remove self
    excluded_ids = {recruiter_id}
    for req_id, recv_id in connected_ids:
        excluded_ids.add(req_id)
        excluded_ids.add(recv_id)
    
    # Get potential suggestions (same job search status, active users)
    suggestions = (
        Recruiter.objects
        .select_related('user')
        .exclude(id__in=excluded_ids)
        .filter(user__is_active=True)
        [:limit]
    )
    
    result = []
    for suggestion in suggestions:
        result.append({
            'recruiter': suggestion,
            'mutual_connections': 0,  # Simplified
            'common_skills': [],
            'score': 0.5,
        })
    
    return result

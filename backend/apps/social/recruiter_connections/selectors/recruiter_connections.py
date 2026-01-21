from typing import Optional

from django.db.models import QuerySet, Q

from apps.social.recruiter_connections.models import RecruiterConnection


def get_recruiter_connections(
    recruiter_id: int,
    status: Optional[str] = 'accepted',
) -> QuerySet[RecruiterConnection]:
    """
    Get connections for a recruiter.
    
    Args:
        recruiter_id: Recruiter ID
        status: Filter by status (default: accepted)
        
    Returns:
        QuerySet of RecruiterConnection
    """
    queryset = (
        RecruiterConnection.objects
        .filter(
            Q(requester_id=recruiter_id) | Q(receiver_id=recruiter_id)
        )
        .select_related('requester__user', 'receiver__user')
    )
    
    if status:
        queryset = queryset.filter(status=status)
    
    return queryset.order_by('-created_at')


def get_connection_by_id(connection_id: int) -> Optional[RecruiterConnection]:
    """
    Get single connection by ID.
    
    Args:
        connection_id: Connection ID
        
    Returns:
        RecruiterConnection or None
    """
    try:
        return (
            RecruiterConnection.objects
            .select_related('requester__user', 'receiver__user')
            .get(id=connection_id)
        )
    except RecruiterConnection.DoesNotExist:
        return None


def get_pending_connections(recruiter_id: int) -> QuerySet[RecruiterConnection]:
    """
    Get pending connection requests received by a recruiter.
    
    Args:
        recruiter_id: Recruiter ID (receiver)
        
    Returns:
        QuerySet of pending RecruiterConnection
    """
    return (
        RecruiterConnection.objects
        .filter(
            receiver_id=recruiter_id,
            status=RecruiterConnection.Status.PENDING
        )
        .select_related('requester__user', 'receiver__user')
        .order_by('-created_at')
    )


def get_sent_pending_connections(recruiter_id: int) -> QuerySet[RecruiterConnection]:
    """
    Get pending connection requests sent by a recruiter.
    
    Args:
        recruiter_id: Recruiter ID (requester)
        
    Returns:
        QuerySet of pending RecruiterConnection
    """
    return (
        RecruiterConnection.objects
        .filter(
            requester_id=recruiter_id,
            status=RecruiterConnection.Status.PENDING
        )
        .select_related('requester__user', 'receiver__user')
        .order_by('-created_at')
    )


def get_connection_count(recruiter_id: int) -> dict:
    """
    Get connection counts for a recruiter.
    
    Args:
        recruiter_id: Recruiter ID
        
    Returns:
        dict with connection counts
    """
    base_query = RecruiterConnection.objects.filter(
        Q(requester_id=recruiter_id) | Q(receiver_id=recruiter_id)
    )
    
    return {
        'total': base_query.filter(status=RecruiterConnection.Status.ACCEPTED).count(),
        'pending_received': RecruiterConnection.objects.filter(
            receiver_id=recruiter_id,
            status=RecruiterConnection.Status.PENDING
        ).count(),
        'pending_sent': RecruiterConnection.objects.filter(
            requester_id=recruiter_id,
            status=RecruiterConnection.Status.PENDING
        ).count(),
    }


def check_connection_status(recruiter1_id: int, recruiter2_id: int) -> Optional[str]:
    """
    Check connection status between two recruiters.
    
    Args:
        recruiter1_id: First recruiter ID
        recruiter2_id: Second recruiter ID
        
    Returns:
        Connection status or None if not connected
    """
    connection = RecruiterConnection.objects.filter(
        Q(requester_id=recruiter1_id, receiver_id=recruiter2_id) |
        Q(requester_id=recruiter2_id, receiver_id=recruiter1_id)
    ).first()
    
    return connection.status if connection else None

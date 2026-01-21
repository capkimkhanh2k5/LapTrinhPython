from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from .models import JobSearchHistory
from .serializers import JobSearchHistorySerializer
from .selectors.job_search_history import list_search_history
from .services.job_search_history import clear_history


class JobSearchHistoryViewSet(viewsets.GenericViewSet):
    """
        ViewSet for Job Search History
    """
    permission_classes = [IsAuthenticated]
    queryset = JobSearchHistory.objects.none() # Placeholder
    serializer_class = JobSearchHistorySerializer
    
    def list(self, request):
        history = list_search_history(request.user)
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        clear_history(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        """
            Xóa một lịch sử tìm kiếm cụ thể
        """
        try:
            item = JobSearchHistory.objects.get(id=pk, user=request.user)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except JobSearchHistory.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

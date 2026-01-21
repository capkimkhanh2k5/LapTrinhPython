from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from .models import AnalyticsReport
from .serializers import AnalyticsReportSerializer
from .selectors.reports import list_reports
from .services.reports import generate_report


class AnalyticsReportViewSet(viewsets.GenericViewSet):
    """ViewSet for Analytics Reports"""
    queryset = AnalyticsReport.objects.all()
    serializer_class = AnalyticsReportSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
            List all analytics reports
        """
        reports = list_reports(request.user, filters=request.query_params.dict())
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)
        
    def retrieve(self, request, pk=None):
        try:
            instance = self.get_object()

            # Kiểm tra xem người dùng có quyền truy cập vào report không
            if not request.user.is_staff and instance.company != request.user.company_profile:
                return Response(status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
            Trigger report generation
        """
        try:
            # Tạo report
            report = generate_report(
                user=request.user,
                report_type_code=request.data.get('report_type'),
                period_start=request.data.get('period_start'),
                period_end=request.data.get('period_end'),
                company=getattr(request.user, 'company_profile', None)
            )
            return Response(
                AnalyticsReportSerializer(report).data, 
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

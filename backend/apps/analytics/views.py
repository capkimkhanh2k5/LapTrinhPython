from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from apps.analytics.models import GeneratedReport
from apps.analytics.serializers import GeneratedReportSerializer
from apps.analytics.services import ReportService
from apps.analytics.selectors import DashboardSelector

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='admin')
    def admin_stats(self, request):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        data = DashboardSelector.get_admin_overview()
        return Response(data)
    
    @action(detail=False, methods=['get'], url_path='company')
    def company_stats(self, request):
        """
        Get high-level stats for company dashboard
        """
        user = request.user
        company = None
        
        # Check if user is Company Owner
        company_profile = getattr(user, 'company_profile', None)
        if company_profile:
            company = company_profile
            
        # If no company context found, return Forbidden or Empty
        if not company:
            return Response(
                {'error': 'User is not associated with any company'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            data = DashboardSelector.get_company_overview(company)
            return Response(data)
        except Exception as e:
            return Response(
                {'error': f'Error fetching stats: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = GeneratedReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GeneratedReport.objects.filter(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        report_type = request.data.get('type')
        if not report_type:
            return Response({'error': 'Type required'}, status=status.HTTP_400_BAD_REQUEST)
            
        report = ReportService.generate_csv_report(
            user=request.user, 
            report_type=report_type,
            filters=request.data.get('filters')
        )
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

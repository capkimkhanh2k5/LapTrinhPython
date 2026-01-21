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

    #TODO: Cần điều chỉnh cho phù hợp với hệ thống hiện tại
    
    @action(detail=False, methods=['get'], url_path='company')
    def company_stats(self, request):
        # Assuming user is linked to a company (need to check implementation detail of Company user)
        # Ideally: request.user.company or check Recruiter profile.
        # For strict compliance, checking if user has 'company' attribute or is a recruiter
        if not hasattr(request.user, 'company_profile'): # Adjust based on actual User model
             # Fallback/Dummy check for demo if Company Profile not linked directly to User
             # Assuming standard Recruiter implementation
             pass
        
        # For now, return empty or mock if company not found to avoid crashing
        # Real implementation depends on where Company is stored on User
        return Response({'status': 'Company stats implementation pending user-company check'})

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

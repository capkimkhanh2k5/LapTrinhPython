import csv
import io
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from apps.analytics.models import GeneratedReport
from apps.analytics.selectors import DashboardSelector
from apps.company.companies.utils.cloudinary import save_raw_file

class ReportService:
    @staticmethod
    def generate_csv_report(user, report_type, filters=None):
        """
        Generate a CSV report and upload to Cloudinary
        """
        if filters is None:
            filters = {}

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        if report_type == GeneratedReport.Type.REVENUE:
            writer.writerow(['Metric', 'Value', 'Date'])
            data = DashboardSelector.get_admin_overview()['revenue']
            writer.writerow(['Total Revenue', data['total'], timezone.now().date()])
            writer.writerow(['30 Days Revenue', data['revenue_30d'], timezone.now().date()])
            
        elif report_type == GeneratedReport.Type.USER_GROWTH:
            writer.writerow(['Metric', 'Value'])
            data = DashboardSelector.get_admin_overview()['users']
            writer.writerow(['Total Users', data['total']])
            writer.writerow(['New Users (30d)', data['new_30d']])
            
        else:
            writer.writerow(['Info', 'Report type implementation pending'])

        # Create temp file for Cloudinary upload
        file_content = buffer.getvalue().encode('utf-8')
        filename = f"report_{report_type}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        temp_file = SimpleUploadedFile(
            f"{filename}.csv",
            file_content,
            content_type='text/csv'
        )
        
        # Upload to Cloudinary
        url = save_raw_file('reports', temp_file, f'report_{report_type}')
        
        report = GeneratedReport.objects.create(
            name=f"{report_type.title()} Report",
            report_type=report_type,
            file=url,
            filters=filters,
            created_by=user
        )
        
        return report


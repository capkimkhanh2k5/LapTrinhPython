from datetime import date
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ..models import AnalyticsReport
from apps.system.report_types.models import ReportType
from apps.company.companies.models import Company

User = get_user_model()

class AnalyticsReportViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='password123',
            first_name='Recruiter',
            last_name='User'
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User'
        )
        
        # Setup Company Profile for user
        self.company = Company.objects.create(
            user=self.user,
            company_name='Test Company',
            tax_code='123456789',
            slug='test-company'
        )
        # Mocking generic relation on user if needed (assuming user.company_profile exists through OneToOne or similar)
        # In this project, Company has OneToOne/ForeignKey with User? Let's check model if tests fail.
        # Assuming for now based on views logic: getattr(request.user, 'company_profile', None)
        
        self.report_type = ReportType.objects.create(
            type_name='JOB_PERFORMANCE',
            description='Stats about job views and applications'
        )
        
        self.list_url = reverse('analytics-reports-list')
        self.generate_url = reverse('analytics-reports-generate')

    def test_generate_report(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'report_type': 'JOB_PERFORMANCE',
            'period_start': '2023-01-01',
            'period_end': '2023-01-31'
        }
        response = self.client.post(self.generate_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AnalyticsReport.objects.count(), 1)
        report = AnalyticsReport.objects.first()
        self.assertEqual(report.generated_by, self.user)
        self.assertEqual(report.company, self.company)

    def test_list_reports_company_scope(self):
        # Report for this company
        AnalyticsReport.objects.create(
            company=self.company,
            report_type=self.report_type,
            report_period_start=date(2023,1,1),
            report_period_end=date(2023,1,31),
            metrics={},
            generated_by=self.user
        )
        # Report for another company
        other_user = User.objects.create_user(email='other@test.com', password='px')
        other_company = Company.objects.create(
            user=other_user, 
            company_name='Other Co', 
            tax_code='999',
            slug='other-co'
        )
        AnalyticsReport.objects.create(
            company=other_company,
            report_type=self.report_type,
            report_period_start=date(2023,1,1),
            report_period_end=date(2023,1,31),
            metrics={},
            generated_by=other_user
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company'], self.company.id)

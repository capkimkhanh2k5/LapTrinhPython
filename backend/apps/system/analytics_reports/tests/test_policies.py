from django.test import TestCase
from apps.system.analytics_reports.policies import AnalyticsReportPolicy
from apps.system.analytics_reports.models import AnalyticsReport
from apps.system.report_types.models import ReportType
from apps.core.users.models import CustomUser
from apps.company.companies.models import Company

class AnalyticsPolicyTest(TestCase):
    def setUp(self):
        # Users
        self.admin = CustomUser.objects.create(email='admin@test.com', is_staff=True, is_superuser=True)
        self.staff = CustomUser.objects.create(email='staff@test.com', is_staff=True)
        self.user_company_a = CustomUser.objects.create(email='company_a@test.com')
        self.user_company_b = CustomUser.objects.create(email='company_b@test.com')
        self.recruiter = CustomUser.objects.create(email='recruiter@test.com')
        
        # Companies
        self.company_a = Company.objects.create(user=self.user_company_a, company_name='A', slug='a')
        self.company_b = Company.objects.create(user=self.user_company_b, company_name='B', slug='b')
        
        # Reports
        self.rpt_type = ReportType.objects.create(type_name='Daily')
        self.report_a = AnalyticsReport.objects.create(
            company=self.company_a, 
            report_type=self.rpt_type,
            report_period_start='2024-01-01',
            report_period_end='2024-01-01',
            metrics={}
        )
        self.report_b = AnalyticsReport.objects.create(
            company=self.company_b, 
            report_type=self.rpt_type,
            report_period_start='2024-01-01',
            report_period_end='2024-01-01',
            metrics={}
        )
        
    def test_admin_staff_scope(self):
        """Admin/Staff should see all reports"""
        qs = AnalyticsReport.objects.all()
        
        admin_qs = AnalyticsReportPolicy.scope(self.admin, qs)
        self.assertEqual(admin_qs.count(), 2)
        
        staff_qs = AnalyticsReportPolicy.scope(self.staff, qs)
        self.assertEqual(staff_qs.count(), 2)

    def test_company_scope(self):
        """Company should only see their reports"""
        qs = AnalyticsReport.objects.all()
        
        # Company A sees A
        qs_a = AnalyticsReportPolicy.scope(self.user_company_a, qs)
        self.assertEqual(qs_a.count(), 1)
        self.assertEqual(qs_a.first(), self.report_a)
        
        # Company B sees B
        qs_b = AnalyticsReportPolicy.scope(self.user_company_b, qs)
        self.assertEqual(qs_b.count(), 1)
        self.assertEqual(qs_b.first(), self.report_b)

    def test_recruiter_scope(self):
        """Recruiter should see nothing"""
        qs = AnalyticsReport.objects.all()
        qs_rec = AnalyticsReportPolicy.scope(self.recruiter, qs)
        self.assertEqual(qs_rec.count(), 0)

    def test_can_view_method(self):
        """Test can_view single object check"""
        # Admin can view anyone
        self.assertTrue(AnalyticsReportPolicy.can_view(self.admin, self.report_a))
        
        # Company A viewing A -> True
        self.assertTrue(AnalyticsReportPolicy.can_view(self.user_company_a, self.report_a))
        
        # Company A viewing B -> False
        self.assertFalse(AnalyticsReportPolicy.can_view(self.user_company_a, self.report_b))
        
        # Recruiter viewing A -> False
        self.assertFalse(AnalyticsReportPolicy.can_view(self.recruiter, self.report_a))

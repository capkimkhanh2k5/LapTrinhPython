from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from apps.core.users.models import CustomUser
from apps.recruitment.jobs.models import Job
from apps.recruitment.applications.models import Application
from apps.billing.models import Transaction, CompanySubscription

class DashboardSelector:
    @staticmethod
    def get_admin_overview():
        """
        Get high-level stats for admin dashboard
        """
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        total_users = CustomUser.objects.count()
        new_users_30d = CustomUser.objects.filter(date_joined__gte=thirty_days_ago).count()
        
        total_jobs = Job.objects.count()
        active_jobs = Job.objects.filter(status=Job.Status.PUBLISHED).count()

        total_revenue = Transaction.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
        revenue_30d = Transaction.objects.filter(
            status='completed', 
            created_at__gte=thirty_days_ago
        ).aggregate(total=Sum('amount'))['total'] or 0

        return {
            'users': {
                'total': total_users,
                'new_30d': new_users_30d,
            },
            'jobs': {
                'total': total_jobs,
                'active': active_jobs,
            },
            'revenue': {
                'total': total_revenue,
                'revenue_30d': revenue_30d
            }
        }

    @staticmethod
    def get_company_overview(company) -> dict:
        """
        Get stats for a specific company
        """
        if not company:
            return {}

        # Jobs
        total_jobs = Job.objects.filter(company=company).count()
        active_jobs = Job.objects.filter(company=company, status=Job.Status.PUBLISHED).count()
        
        # Applications
        total_applications = Application.objects.filter(job__company=company).count()
        
        # Subscription
        plan_name = "Free"
        try:
            # Check for active subscription
            current_sub = CompanySubscription.objects.filter(
                company=company, 
                is_active=True,
                end_date__gte=timezone.now()
            ).first()
            
            if current_sub and current_sub.plan:
                plan_name = current_sub.plan.name
        except Exception:
            # Fallback to defaults on error (e.g. Models missing)
            pass

        return {
            'jobs': {
                'total': total_jobs,
                'active': active_jobs
            },
            'applications': {
                'total': total_applications
            },
            'subscription': {
                'plan': plan_name
            }
        }

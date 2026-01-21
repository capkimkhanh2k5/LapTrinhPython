from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


router = DefaultRouter()


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    
    # Users app routes (login, logout, register, user management)
    path('api/users/', include('apps.core.users.urls')),
    
    # Company app routes (includes nested benefits)
    # Company Followers routes (must be before generic company routes)
    path('api/companies/', include('apps.social.company_followers.urls')),
    path('api/companies/', include('apps.company.companies.urls')),
    # Company Media nested routes
    path('api/companies/', include('apps.company.company_media.urls')),
    
    # Jobs routes (Module 4 - CRITICAL)
    path('api/jobs/', include('apps.recruitment.jobs.urls')),
    
    # Recruiter app routes
    path('api/recruiters/', include('apps.candidate.recruiters.urls')),
    # Recruiter Education nested routes
    path('api/recruiters/<int:recruiter_id>/education/', include('apps.candidate.recruiter_education.urls')),
    # Recruiter Experience nested routes
    path('api/recruiters/<int:recruiter_id>/experience/', include('apps.candidate.recruiter_experience.urls')),
    # Recruiter Skills nested routes
    path('api/recruiters/<int:recruiter_id>/skills/', include('apps.candidate.recruiter_skills.urls')),
    # Recruiter Certifications nested routes
    path('api/recruiters/<int:recruiter_id>/certifications/', include('apps.candidate.recruiter_certifications.urls')),
    # Recruiter Languages nested routes
    path('api/recruiters/<int:recruiter_id>/languages/', include('apps.candidate.recruiter_languages.urls')),
    # Recruiter Projects nested routes
    path('api/recruiters/<int:recruiter_id>/projects/', include('apps.candidate.recruiter_projects.urls')),
    
    # Languages public routes
    path('api/languages/', include('apps.candidate.languages.urls')),
    
    # Jobs routes
    path('api/', include('apps.recruitment.campaigns.urls')),
    path('api/applications/', include('apps.recruitment.applications.urls')),
    path('api/', include('apps.recruitment.application_status_history.urls')),
    
    # Billing routes
    path('api/billing/', include('apps.billing.urls')),
    
    # Job Applications nested routes
    path('api/jobs/<int:job_id>/applications/', include('apps.recruitment.applications.urls_nested')),
    
    # Job Skills nested routes
    path('api/jobs/<int:job_id>/skills/', include('apps.recruitment.job_skills.urls')),
    
    # Email routes
    path('api/email/', include('apps.email.urls')),
    
    # Blog routes
    path('api/blog/', include('apps.blog.urls')),
    
    # System Domaintions nested routes
    path('api/jobs/<int:job_id>/locations/', include('apps.recruitment.job_locations.urls')),
    
    # Saved Jobs routes
    path('api/saved-jobs/', include('apps.recruitment.saved_jobs.urls')),
    # Recruiter Saved Jobs nested routes
    path('api/recruiters/<int:recruiter_id>/saved-jobs/', 
         include('apps.recruitment.saved_jobs.urls_nested')),
    
    # Interviews routes
    path('api/interviews/', include('apps.recruitment.interviews.urls')),
    
    # Interview Types routes
    path('api/interview-types/', include('apps.recruitment.interview_types.urls')),
    
    # CV Templates routes (CV Builder Module)
    path('api/cv-templates/', include('apps.candidate.cv_templates.urls')),
    
    # Recruiter CVs nested routes
    path('api/recruiters/<int:recruiter_id>/cvs/', include('apps.candidate.recruiter_cvs.urls')),
    
    # Industries routes (Taxonomy)
    path('api/industries/', include('apps.company.industries.urls')),
    
    # Job Categories routes (Taxonomy)
    path('api/job-categories/', include('apps.recruitment.job_categories.urls')),
    
    # Skills routes (Taxonomy)
    path('api/skills/', include('apps.candidate.skills.urls')),
    
    # Benefit Categories routes
    path('api/benefit-categories/', include('apps.company.benefit_categories.urls')),
    
    # Geography routes
    path('api/provinces/', include('apps.geography.provinces.urls')),
    path('api/communes/', include('apps.geography.communes.urls')),
    path('api/addresses/', include('apps.geography.addresses.urls')),
    
    # Assessment Module 10-11: AI Matching, Tests, Results
    path('api/', include('apps.assessment.ai_matching_scores.urls')),
    path('api/assessment-tests/', include('apps.assessment.assessment_tests.urls')),
    path('api/test-results/', include('apps.assessment.test_results.urls')),
    
    # Reviews, Connections, Recommendations
    path('api/reviews/', include('apps.social.reviews.urls')),
    path('api/connections/', include('apps.social.recruiter_connections.urls')),
    path('api/recommendations/', include('apps.social.recommendations.urls')),
    
    # Notifications & Messages
    path('api/notifications/', include('apps.communication.notifications.urls')),
    path('api/messages/', include('apps.communication.message_threads.urls')),
    path('api/messages/', include('apps.communication.messages.urls')),
    
    # Job Alerts
    path('api/', include('apps.communication.job_alerts.urls')),
    
    # JWT Token endpoints (built-in)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('apps.recruitment.referrals.urls')),
    
    # System & Administration
    path('api/system-settings/', include('apps.system.system_settings.urls')),
    path('api/activity-logs/', include('apps.system.activity_logs.urls')),
    path('api/file-uploads/', include('apps.system.file_uploads.urls')),
    
    # Advanced Features
    path('api/search-history/', include('apps.system.job_search_history.urls')),
    
    # Analytics & Reporting
    path('api/dashboard/', include('apps.analytics.urls')),
    
    # Media Types
    path('api/media-types/', include('apps.company.media_types.urls')),
]


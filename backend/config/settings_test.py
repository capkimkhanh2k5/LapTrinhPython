"""
Settings cho chạy tests - chỉ bao gồm apps cần thiết
"""
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'test-secret-key-for-testing-only'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    # Core 
    'apps.core.users',
    # Blog Domain
    'apps.blog',
    # 'apps.blog.blog_posts',
    # 'apps.blog.blog_categories',
    # 'apps.blog.blog_tags',
    # 'apps.blog.blog_post_tags',
    # 'apps.blog.blog_comments',
    # Company Domain (cho company tests)
    'apps.company.companies',
    'apps.company.industries',
    'apps.company.benefit_categories',
    'apps.company.company_benefits',
    'apps.company.media_types',
    'apps.company.company_media',
    # Geography Domain (FK dependencies)
    'apps.geography.provinces',
    'apps.geography.communes',
    'apps.geography.addresses',
    # System Domain (FK dependencies cho Activity Logs)
    'apps.system.activity_logs',
    'apps.system.activity_log_types',
    'apps.system.system_settings',
    'apps.system.file_uploads',
    'apps.analytics',
    # 'apps.system.analytics_reports',
    # 'apps.system.analytics_daily_statistics',
    # 'apps.system.report_types',
    # 'apps.system.reports',
    'apps.system.audit_logs',
    'apps.system.search_history',
    'apps.system.faqs',
    'apps.system.job_search_history',
    # Candidate Domain (recruiters, education, experience, skills, certifications, languages, projects)
    'apps.candidate.recruiters',
    'apps.candidate.recruiter_education',
    'apps.candidate.recruiter_experience',
    'apps.candidate.recruiter_skills',
    'apps.candidate.recruiter_certifications',
    'apps.candidate.recruiter_languages',
    'apps.candidate.recruiter_projects',
    'apps.candidate.skill_categories',
    'apps.candidate.skills',
    'apps.candidate.languages',
    # Social Domain (full - for Module 12)
    'apps.social.company_followers',
    'apps.social.skill_endorsements',
    'apps.social.reviews',
    'apps.social.review_reactions',
    'apps.social.recruiter_connections',
    'apps.social.recommendations',
    # Recruitment Domain (jobs)
    'apps.recruitment.jobs',
    'apps.recruitment.job_categories',
    'apps.recruitment.applications',
    'apps.recruitment.application_status_history',
    'apps.recruitment.campaigns',
    'apps.recruitment.referrals',
    'apps.billing',
    'apps.recruitment.job_skills',
    'apps.recruitment.job_locations',
    'apps.recruitment.saved_jobs',
    'apps.recruitment.job_views',
    'apps.recruitment.interviews',
    'apps.recruitment.interview_types',
    'apps.recruitment.interview_interviewers',
    # Candidate Domain (CV Builder)
    'apps.candidate.cv_templates',
    'apps.candidate.cv_template_categories',
    'apps.candidate.recruiter_cvs',
    # Assessment Domain (for AI Matching)
    'apps.assessment.assessment_categories',
    'apps.assessment.assessment_tests',
    'apps.assessment.test_results',
    'apps.assessment.ai_matching_scores',
    'apps.assessment.job_assessment_requirements',
    'apps.email',
    'apps.communication.notifications',
    'apps.communication.notification_types',
    'apps.communication.messages',
    'apps.communication.message_threads',
    'apps.communication.message_participants',
    'apps.communication.job_alerts',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database - dùng SQLite cho local tests (không cần Docker)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core_users.CustomUser'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Tắt password hashers nặng để test nhanh hơn
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ===== VN Pay Configuration (TestDummy) =====
VNP_TMN_CODE = "EMBIL7EU"
VNP_HASH_SECRET = "FP2480JF752TUW5PZWV8MSHCE4FAWB2V"
VNP_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
VNP_RETURN_URL = "http://localhost:3000/billing/payment-return"

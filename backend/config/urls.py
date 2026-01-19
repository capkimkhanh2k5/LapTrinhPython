"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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
    
    # Recruiter app routes
    path('api/recruiters/', include('apps.candidate.recruiters.urls')),
    # Recruiter Education nested routes
    path('api/recruiters/<int:recruiter_id>/education/', include('apps.candidate.recruiter_education.urls')),
    # Recruiter Experience nested routes
    path('api/recruiters/<int:recruiter_id>/experience/', include('apps.candidate.recruiter_experience.urls')),
    
    # JWT Token endpoints (built-in)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

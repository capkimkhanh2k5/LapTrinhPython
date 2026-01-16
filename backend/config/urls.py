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
from django.urls import path

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.users.views import UserViewSet, EmployerProfileViewSet, CandidateProfileViewSet
from apps.jobs.views import JobViewSet, CategoryViewSet
from apps.applications.views import ApplicationViewSet

router = DefaultRouter()
# router.register(r'users', UserViewSet)     -> Moved to apps/users/urls.py
# router.register(r'employers', EmployerProfileViewSet)
# router.register(r'candidates', CandidateProfileViewSet)
router.register(r'jobs', JobViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'applications', ApplicationViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/users/', include('apps.users.urls')), # Modular include
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

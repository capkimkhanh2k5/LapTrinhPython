from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardViewSet, ReportViewSet

router = DefaultRouter()
router.register(r'stats', DashboardViewSet, basename='dashboard')
router.register(r'reports', ReportViewSet, basename='reports')

urlpatterns = [
    path('', include(router.urls)),
]

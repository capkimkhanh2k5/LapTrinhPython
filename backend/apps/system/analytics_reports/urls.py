from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnalyticsReportViewSet

router = DefaultRouter()
router.register(r'', AnalyticsReportViewSet, basename='analytics-reports')

urlpatterns = [
    path('', include(router.urls)),
]

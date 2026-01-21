from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.assessment.test_results.views import TestResultViewSet


router = DefaultRouter()
router.register(r'', TestResultViewSet, basename='test-results')

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.assessment.assessment_tests.views import AssessmentTestViewSet


router = DefaultRouter()
router.register(r'', AssessmentTestViewSet, basename='assessment-tests')

urlpatterns = [
    # All endpoints handled by ViewSet (CRUD + custom @actions)
    path('', include(router.urls)),
]

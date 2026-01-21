from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewSet
from apps.assessment.ai_matching_scores.views import MatchingCandidatesView
from apps.assessment.test_results.views import JobRequiredTestsView

router = DefaultRouter()
router.register(r'', JobViewSet, basename='jobs')

app_name = 'jobs'

urlpatterns = [
    path('<int:job_id>/matching-candidates', MatchingCandidatesView.as_view({'get': 'list'}), name='matching-candidates'),
    path('<int:job_id>/required-tests', JobRequiredTestsView.as_view({'get': 'list'}), name='job-required-tests'),
    path('', include(router.urls)),
]

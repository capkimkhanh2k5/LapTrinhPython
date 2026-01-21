from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecruiterViewSet
from apps.assessment.ai_matching_scores.views import MatchingJobsView
from apps.assessment.test_results.views import RecruiterTestResultsView
from apps.social.reviews.views import RecruiterReviewsView
from apps.social.recruiter_connections.views import RecruiterConnectionsView, SendConnectionView
from apps.social.recommendations.views import RecruiterRecommendationsView, WriteRecommendationView

router = DefaultRouter()
router.register(r'', RecruiterViewSet, basename='recruiter')

app_name = 'recruiters'

urlpatterns = [
    path('<int:recruiter_id>/matching-jobs', MatchingJobsView.as_view({'get': 'list'}), name='matching-jobs'),
    path('<int:recruiter_id>/test-results', RecruiterTestResultsView.as_view({'get': 'list'}), name='recruiter-test-results'),
    path('<int:recruiter_id>/reviews/', RecruiterReviewsView.as_view({'get': 'list'}), name='recruiter-reviews'),
    path('<int:recruiter_id>/connections/', RecruiterConnectionsView.as_view({'get': 'list'}), name='recruiter-connections'),
    path('<int:recruiter_id>/connect/', SendConnectionView.as_view({'post': 'create'}), name='recruiter-connect'),
    path('<int:recruiter_id>/recommendations/', RecruiterRecommendationsView.as_view({'get': 'list'}), name='recruiter-recommendations'),
    path('<int:recruiter_id>/recommend/', WriteRecommendationView.as_view({'post': 'create'}), name='recruiter-recommend'),
    path('', include(router.urls)),
]

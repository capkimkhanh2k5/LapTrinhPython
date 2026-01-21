from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.assessment.ai_matching_scores.views import AIMatchingViewSet

app_name = 'ai_matching_scores'

router = DefaultRouter()
router.register(r'ai-matching', AIMatchingViewSet, basename='ai-matching')

urlpatterns = [
    path('', include(router.urls)),
]

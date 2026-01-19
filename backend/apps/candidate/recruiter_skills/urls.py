from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecruiterSkillViewSet

router = DefaultRouter()
router.register(r'', RecruiterSkillViewSet, basename='recruiter-skills')

app_name = 'recruiter_skills'

urlpatterns = [
    path('', include(router.urls)),
]

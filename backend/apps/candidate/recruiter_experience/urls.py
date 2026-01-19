from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecruiterExperienceViewSet

router = DefaultRouter()
router.register(r'', RecruiterExperienceViewSet, basename='recruiter-experience')

app_name = 'recruiter_experience'

urlpatterns = [
    path('', include(router.urls)),
]

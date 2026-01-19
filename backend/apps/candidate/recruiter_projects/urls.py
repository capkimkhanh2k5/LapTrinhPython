from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecruiterProjectViewSet

router = DefaultRouter()
router.register(r'', RecruiterProjectViewSet, basename='recruiter-projects')

app_name = 'recruiter_projects'

urlpatterns = [
    path('', include(router.urls)),
]

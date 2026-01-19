from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecruiterEducationViewSet

router = DefaultRouter()
router.register(r'', RecruiterEducationViewSet, basename='recruiter-education')

app_name = 'recruiter_education'

urlpatterns = [
    path('', include(router.urls)),
]

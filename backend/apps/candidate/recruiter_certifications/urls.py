from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecruiterCertificationViewSet

router = DefaultRouter()
router.register(r'', RecruiterCertificationViewSet, basename='recruiter-certifications')

app_name = 'recruiter_certifications'

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, EmployerProfileViewSet, CandidateProfileViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'employers', EmployerProfileViewSet, basename='employer')
router.register(r'candidates', CandidateProfileViewSet, basename='candidate')

urlpatterns = [
    path('', include(router.urls)),
]

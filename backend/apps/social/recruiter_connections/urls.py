from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.social.recruiter_connections.views import ConnectionViewSet


router = DefaultRouter()
router.register(r'', ConnectionViewSet, basename='connections')

urlpatterns = [
    path('', include(router.urls)),
]

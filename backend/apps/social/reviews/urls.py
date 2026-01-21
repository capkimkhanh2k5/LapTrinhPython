from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.social.reviews.views import ReviewViewSet


router = DefaultRouter()
router.register(r'', ReviewViewSet, basename='reviews')

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MediaTypeViewSet

router = DefaultRouter()
router.register(r'', MediaTypeViewSet, basename='media-types')

urlpatterns = [
    path('', include(router.urls)),
]

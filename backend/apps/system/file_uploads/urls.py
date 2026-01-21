from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileUploadViewSet

router = DefaultRouter()
router.register(r'', FileUploadViewSet, basename='file-uploads')

urlpatterns = [
    path('', include(router.urls)),
]

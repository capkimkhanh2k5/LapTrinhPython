# MessageThread URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageThreadViewSet

router = DefaultRouter()
router.register(r'threads', MessageThreadViewSet, basename='message-thread')

app_name = 'message_threads'

urlpatterns = [
    path('', include(router.urls)),
]

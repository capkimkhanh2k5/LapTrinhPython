from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobSearchHistoryViewSet

router = DefaultRouter()
router.register(r'', JobSearchHistoryViewSet, basename='search-history')

urlpatterns = [
    path('', include(router.urls)),
]

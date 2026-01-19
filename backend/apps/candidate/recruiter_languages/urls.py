from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecruiterLanguageViewSet

router = DefaultRouter()
router.register(r'', RecruiterLanguageViewSet, basename='recruiter-languages')

app_name = 'recruiter_languages'

urlpatterns = [
    path('', include(router.urls)),
]

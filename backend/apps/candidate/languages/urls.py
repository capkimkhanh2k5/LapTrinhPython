from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LanguageViewSet

router = DefaultRouter()
router.register(r'', LanguageViewSet, basename='languages')

app_name = 'languages'

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.email.views import EmailTemplateCategoryViewSet, EmailTemplateViewSet, SentEmailViewSet

router = DefaultRouter()
router.register(r'template-categories', EmailTemplateCategoryViewSet)
router.register(r'templates', EmailTemplateViewSet)
router.register(r'logs', SentEmailViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

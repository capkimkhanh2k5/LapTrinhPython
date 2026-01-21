from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.blog.views import PostViewSet, CategoryViewSet, TagViewSet

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import models

from apps.blog.models import Post, Category, Tag
from apps.blog.serializers import PostSerializer, CategorySerializer, TagSerializer
from apps.core.permissions import IsAdminOrReadOnly
from apps.blog.services import BlogService
from apps.blog.selectors import BlogSelector

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated] # Allow all authenticated users (logic limited in perform_create)
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'summary', 'content', 'tags__name', 'category__name']
    ordering_fields = ['published_at', 'view_count', 'created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # Staff sees all
            if user.is_staff:
                return BlogSelector.get_all_posts_for_admin()
            # Regular user sees enabled public posts AND their own posts
            # Logic: (Public) OR (My Posts)
            return Post.objects.filter(
                models.Q(status=Post.Status.PUBLISHED) | 
                models.Q(author=user)
            ).distinct()
            
        return BlogSelector.get_public_posts()

    def perform_create(self, serializer):
        user = self.request.user
        company = None
        status_val = Post.Status.DRAFT # Default to Draft for review
        
        # Determine Company
        company_profile = getattr(user, 'company_profile', None)
        if company_profile:
            company = company_profile
        else:
            recruiter_profile = getattr(user, 'recruiter_profile', None)
            if recruiter_profile:
                company = recruiter_profile.current_company # Recruiter model field name check needed
                
        # If Admin, allow Publish immediately
        if user.is_staff:
            status_val = serializer.validated_data.get('status', Post.Status.PUBLISHED)
            
        serializer.save(
            author=user,
            company=company,
            status=status_val
        )

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, slug=None):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
            
        post = self.get_object()
        BlogService.publish_post(post)
        return Response({'status': 'published', 'published_at': post.published_at})

    @action(detail=True, methods=['post'], url_path='view', permission_classes=[AllowAny])
    def view_count(self, request, slug=None):
        post = self.get_object()
        new_count = BlogService.increment_view_count(post)
        return Response({'view_count': new_count})

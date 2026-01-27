from django.utils import timezone
from django.core.exceptions import PermissionDenied
from apps.blog.models import Post

class BlogService:
    @staticmethod
    def create_post(author, data):
        """
        Create a new blog post.
        
        Args:
            author: The user creating the post (must have 'blog.add_post' permission)
            data: Validated dict of post fields
            
        Raises:
            PermissionDenied: If user lacks permission to create posts
        """
        # Strict ownership: Only users with blog.add_post permission can create
        if not author.has_perm('blog.add_post'):
            raise PermissionDenied("You do not have permission to create blog posts.")
        
        return Post.objects.create(author=author, **data)

    @staticmethod
    def publish_post(post: Post) -> Post:
        post.status = Post.Status.PUBLISHED
        post.published_at = timezone.now()
        post.save()
        return post

    @staticmethod
    def increment_view_count(post: Post) -> int:
        post.view_count += 1
        post.save(update_fields=['view_count'])
        return post.view_count

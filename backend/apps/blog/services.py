from django.utils import timezone
from apps.blog.models import Post

class BlogService:
    @staticmethod
    def create_post(author, data):
        #TODO: Cần xem lại logic này, Post thuộc user

        # Logic to create post
        # data should be validated dict
        # Assuming serializer validation happens before
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

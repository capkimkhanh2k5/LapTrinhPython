from apps.blog.models import Post, Category, Tag

class BlogSelector:
    @staticmethod
    def get_public_posts():
        """Get all published posts for public view"""
        return Post.objects.filter(status=Post.Status.PUBLISHED).select_related('author', 'category').prefetch_related('tags')

    @staticmethod
    def get_all_posts_for_admin():
        """Get all posts for admin (drafts included)"""
        return Post.objects.all().select_related('author', 'category').prefetch_related('tags')

    @staticmethod
    def get_post_by_slug(slug: str, is_staff: bool = False):
        qs = Post.objects.select_related('author', 'category').prefetch_related('tags')
        if not is_staff:
            qs = qs.filter(status=Post.Status.PUBLISHED)
        try:
            return qs.get(slug=slug)
        except Post.DoesNotExist:
            return None

from rest_framework import serializers
from apps.blog.models import Post, Category, Tag

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']

class PostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tags', write_only=True, many=True, required=False
    )
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'author_name', 'category', 'category_id', 
            'tags', 'tag_ids', 'summary', 'content', 'thumbnail', 
            'status', 'published_at', 'view_count', 'created_at'
        ]
        read_only_fields = ['author', 'published_at', 'view_count', 'slug']

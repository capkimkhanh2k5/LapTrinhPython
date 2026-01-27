"""
Tests for Media Types Selectors
Module 22: Advanced Features - Media Types API

Test Coverage:
- list_media_types
- get_media_type_by_id
- get_media_type_by_name
"""

from django.test import TestCase
from apps.company.media_types.models import MediaType
from apps.company.media_types.selectors.media_types import (
    list_media_types,
    get_media_type_by_id,
    get_media_type_by_name
)


class TestMediaTypeSelectors(TestCase):
    def setUp(self):
        self.image = MediaType.objects.create(type_name='Image', description='Images', is_active=True)
        self.video = MediaType.objects.create(type_name='Video', description='Videos', is_active=True)
        self.doc = MediaType.objects.create(type_name='Document', description='Docs', is_active=False)

    def test_list_all_media_types(self):
        """Should return all media types"""
        result = list_media_types()
        self.assertEqual(result.count(), 3)
    
    def test_list_active_media_types(self):
        """Should filter by is_active=True"""
        result = list_media_types(is_active=True)
        self.assertEqual(result.count(), 2)
        for item in result:
            self.assertTrue(item.is_active)
    
    def test_list_inactive_media_types(self):
        """Should filter by is_active=False"""
        result = list_media_types(is_active=False)
        self.assertEqual(result.count(), 1)
        self.assertFalse(result.first().is_active)
    
    def test_list_media_types_ordered(self):
        """Should return ordered by type_name"""
        result = list_media_types()
        names = [item.type_name for item in result]
        self.assertEqual(names, sorted(names))
    
    def test_list_media_types_empty(self):
        """Should return empty queryset when no types exist"""
        MediaType.objects.all().delete()
        result = list_media_types()
        self.assertEqual(result.count(), 0)

    def test_get_media_type_by_id_success(self):
        """Should return media type by ID"""
        result = get_media_type_by_id(self.image.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.image.id)
        self.assertEqual(result.type_name, self.image.type_name)
    
    def test_get_media_type_by_id_not_found(self):
        """Should return None for non-existent ID"""
        result = get_media_type_by_id(99999)
        self.assertIsNone(result)

    def test_get_media_type_by_name_success(self):
        """Should return media type by name"""
        result = get_media_type_by_name('Image')
        self.assertIsNotNone(result)
        self.assertEqual(result.type_name, 'Image')
    
    def test_get_media_type_by_name_not_found(self):
        """Should return None for non-existent name"""
        result = get_media_type_by_name('NonExistent')
        self.assertIsNone(result)
    
    def test_get_media_type_by_name_case_sensitive(self):
        """Should be case-sensitive"""
        result = get_media_type_by_name('image')  # lowercase
        self.assertIsNone(result)

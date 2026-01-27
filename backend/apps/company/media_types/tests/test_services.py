"""
Tests for Media Types Services
Module 22: Advanced Features - Media Types API

Test Coverage:
- create_media_type
- update_media_type  
- delete_media_type
"""

from django.test import TestCase
from django.db import IntegrityError

from apps.company.media_types.models import MediaType
from apps.company.media_types.services.media_types import (
    create_media_type,
    update_media_type,
    delete_media_type,
    MediaTypeInput
)


class TestMediaTypeServices(TestCase):
    def setUp(self):
        self.media_type = MediaType.objects.create(
            type_name='Image',
            description='Image files',
            is_active=True
        )

    # ============================================
    # CREATE SERVICE TESTS
    # ============================================

    def test_create_media_type_success(self):
        """Should create media type with valid data"""
        input_data = MediaTypeInput(
            type_name='Video',
            description='Video files (mp4, webm)',
            is_active=True
        )
        
        result = create_media_type(input_data)
        
        self.assertIsNotNone(result.id)
        self.assertEqual(result.type_name, 'Video')
        self.assertEqual(result.description, 'Video files (mp4, webm)')
        self.assertTrue(result.is_active)
    
    def test_create_media_type_without_description(self):
        """Should create media type without description"""
        input_data = MediaTypeInput(
            type_name='Audio',
            is_active=True
        )
        
        result = create_media_type(input_data)
        
        self.assertEqual(result.type_name, 'Audio')
        self.assertEqual(result.description, '')
    
    def test_create_media_type_default_active(self):
        """Should default is_active to True"""
        input_data = MediaTypeInput(type_name='Document')
        
        result = create_media_type(input_data)
        
        self.assertTrue(result.is_active)
    
    def test_create_media_type_duplicate_name_fails(self):
        """Should raise ValueError for duplicate type_name"""
        input_data = MediaTypeInput(
            type_name='Image',  # Already exists
            description='Another image type'
        )
        
        with self.assertRaises(ValueError) as cm:
            create_media_type(input_data)
        
        self.assertIn("already exists", str(cm.exception))

    # ============================================
    # UPDATE SERVICE TESTS
    # ============================================
    
    def test_update_media_type_all_fields(self):
        """Should update all fields"""
        input_data = MediaTypeInput(
            type_name='Updated Name',
            description='Updated description',
            is_active=False
        )
        
        result = update_media_type(self.media_type, input_data)
        
        self.assertEqual(result.type_name, 'Updated Name')
        self.assertEqual(result.description, 'Updated description')
        self.assertFalse(result.is_active)
    
    def test_update_media_type_partial(self):
        """Should update only provided fields"""
        original_name = self.media_type.type_name
        input_data = MediaTypeInput(description='New description only')
        
        result = update_media_type(self.media_type, input_data)
        
        self.assertEqual(result.type_name, original_name)
        self.assertEqual(result.description, 'New description only')
    
    def test_update_media_type_toggle_active(self):
        """Should toggle is_active status"""
        input_data = MediaTypeInput(is_active=False)
        
        result = update_media_type(self.media_type, input_data)
        
        self.assertFalse(result.is_active)
    
    def test_update_media_type_duplicate_name_fails(self):
        """Should raise ValueError when updating to existing name"""
        type1 = MediaType.objects.create(type_name='Type1', is_active=True)
        type2 = MediaType.objects.create(type_name='Type2', is_active=True)
        
        input_data = MediaTypeInput(type_name='Type1')
        
        with self.assertRaises(ValueError) as cm:
            update_media_type(type2, input_data)
        
        self.assertIn("already exists", str(cm.exception))
    
    def test_update_media_type_same_name_allowed(self):
        """Should allow updating with same type_name"""
        input_data = MediaTypeInput(
            type_name=self.media_type.type_name,  # Same name
            description='Updated description'
        )
        
        result = update_media_type(self.media_type, input_data)
        
        self.assertEqual(result.description, 'Updated description')

    # ============================================
    # DELETE SERVICE TESTS
    # ============================================
    
    def test_delete_media_type_success(self):
        """Should delete media type"""
        media_type_id = self.media_type.id
        
        delete_media_type(self.media_type)
        
        self.assertFalse(MediaType.objects.filter(id=media_type_id).exists())
    
    def test_delete_media_type_removes_from_db(self):
        """Should completely remove from database"""
        type1 = MediaType.objects.create(type_name='ToDelete', is_active=True)
        type2 = MediaType.objects.create(type_name='ToKeep', is_active=True)
        
        delete_media_type(type1)
        
        self.assertEqual(MediaType.objects.count(), 2) # setUp creates one too, so 1+2=3, delete 1 -> 2
        self.assertEqual(MediaType.objects.last().type_name, 'ToKeep')

"""
Tests for Media Types Services
Module 22: Advanced Features - Media Types API

Test Coverage:
- create_media_type
- update_media_type  
- delete_media_type
"""

import pytest
from django.db import IntegrityError

from apps.company.media_types.models import MediaType
from apps.company.media_types.services.media_types import (
    create_media_type,
    update_media_type,
    delete_media_type,
    MediaTypeInput
)


@pytest.fixture
def media_type(db):
    """Create sample media type"""
    return MediaType.objects.create(
        type_name='Image',
        description='Image files',
        is_active=True
    )


# ============================================
# CREATE SERVICE TESTS
# ============================================

@pytest.mark.django_db
class TestCreateMediaType:
    """Tests for create_media_type service"""
    
    def test_create_media_type_success(self):
        """Should create media type with valid data"""
        input_data = MediaTypeInput(
            type_name='Video',
            description='Video files (mp4, webm)',
            is_active=True
        )
        
        result = create_media_type(input_data)
        
        assert result.id is not None
        assert result.type_name == 'Video'
        assert result.description == 'Video files (mp4, webm)'
        assert result.is_active is True
    
    def test_create_media_type_without_description(self):
        """Should create media type without description"""
        input_data = MediaTypeInput(
            type_name='Audio',
            is_active=True
        )
        
        result = create_media_type(input_data)
        
        assert result.type_name == 'Audio'
        assert result.description == ''
    
    def test_create_media_type_default_active(self):
        """Should default is_active to True"""
        input_data = MediaTypeInput(type_name='Document')
        
        result = create_media_type(input_data)
        
        assert result.is_active is True
    
    def test_create_media_type_duplicate_name_fails(self, media_type):
        """Should raise ValueError for duplicate type_name"""
        input_data = MediaTypeInput(
            type_name='Image',  # Already exists
            description='Another image type'
        )
        
        with pytest.raises(ValueError) as exc_info:
            create_media_type(input_data)
        
        assert "already exists" in str(exc_info.value)


# ============================================
# UPDATE SERVICE TESTS
# ============================================

@pytest.mark.django_db
class TestUpdateMediaType:
    """Tests for update_media_type service"""
    
    def test_update_media_type_all_fields(self, media_type):
        """Should update all fields"""
        input_data = MediaTypeInput(
            type_name='Updated Name',
            description='Updated description',
            is_active=False
        )
        
        result = update_media_type(media_type, input_data)
        
        assert result.type_name == 'Updated Name'
        assert result.description == 'Updated description'
        assert result.is_active is False
    
    def test_update_media_type_partial(self, media_type):
        """Should update only provided fields"""
        original_name = media_type.type_name
        input_data = MediaTypeInput(description='New description only')
        
        result = update_media_type(media_type, input_data)
        
        assert result.type_name == original_name
        assert result.description == 'New description only'
    
    def test_update_media_type_toggle_active(self, media_type):
        """Should toggle is_active status"""
        input_data = MediaTypeInput(is_active=False)
        
        result = update_media_type(media_type, input_data)
        
        assert result.is_active is False
    
    def test_update_media_type_duplicate_name_fails(self, db):
        """Should raise ValueError when updating to existing name"""
        type1 = MediaType.objects.create(type_name='Type1', is_active=True)
        type2 = MediaType.objects.create(type_name='Type2', is_active=True)
        
        input_data = MediaTypeInput(type_name='Type1')
        
        with pytest.raises(ValueError) as exc_info:
            update_media_type(type2, input_data)
        
        assert "already exists" in str(exc_info.value)
    
    def test_update_media_type_same_name_allowed(self, media_type):
        """Should allow updating with same type_name"""
        input_data = MediaTypeInput(
            type_name=media_type.type_name,  # Same name
            description='Updated description'
        )
        
        result = update_media_type(media_type, input_data)
        
        assert result.description == 'Updated description'


# ============================================
# DELETE SERVICE TESTS
# ============================================

@pytest.mark.django_db
class TestDeleteMediaType:
    """Tests for delete_media_type service"""
    
    def test_delete_media_type_success(self, media_type):
        """Should delete media type"""
        media_type_id = media_type.id
        
        delete_media_type(media_type)
        
        assert not MediaType.objects.filter(id=media_type_id).exists()
    
    def test_delete_media_type_removes_from_db(self, db):
        """Should completely remove from database"""
        type1 = MediaType.objects.create(type_name='ToDelete', is_active=True)
        type2 = MediaType.objects.create(type_name='ToKeep', is_active=True)
        
        delete_media_type(type1)
        
        assert MediaType.objects.count() == 1
        assert MediaType.objects.first().type_name == 'ToKeep'

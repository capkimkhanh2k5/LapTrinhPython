"""
Tests for Media Types Selectors
Module 22: Advanced Features - Media Types API

Test Coverage:
- list_media_types
- get_media_type_by_id
- get_media_type_by_name
"""

import pytest
from apps.company.media_types.models import MediaType
from apps.company.media_types.selectors.media_types import (
    list_media_types,
    get_media_type_by_id,
    get_media_type_by_name
)


@pytest.fixture
def media_types(db):
    """Create multiple media types"""
    types = [
        MediaType.objects.create(type_name='Image', description='Images', is_active=True),
        MediaType.objects.create(type_name='Video', description='Videos', is_active=True),
        MediaType.objects.create(type_name='Document', description='Docs', is_active=False),
    ]
    return types


# ============================================
# LIST SELECTOR TESTS
# ============================================

@pytest.mark.django_db
class TestListMediaTypes:
    """Tests for list_media_types selector"""
    
    def test_list_all_media_types(self, media_types):
        """Should return all media types"""
        result = list_media_types()
        
        assert result.count() == 3
    
    def test_list_active_media_types(self, media_types):
        """Should filter by is_active=True"""
        result = list_media_types(is_active=True)
        
        assert result.count() == 2
        for item in result:
            assert item.is_active is True
    
    def test_list_inactive_media_types(self, media_types):
        """Should filter by is_active=False"""
        result = list_media_types(is_active=False)
        
        assert result.count() == 1
        assert result.first().is_active is False
    
    def test_list_media_types_ordered(self, media_types):
        """Should return ordered by type_name"""
        result = list_media_types()
        names = [item.type_name for item in result]
        
        assert names == sorted(names)
    
    def test_list_media_types_empty(self, db):
        """Should return empty queryset when no types exist"""
        result = list_media_types()
        
        assert result.count() == 0


# ============================================
# GET BY ID SELECTOR TESTS
# ============================================

@pytest.mark.django_db
class TestGetMediaTypeById:
    """Tests for get_media_type_by_id selector"""
    
    def test_get_media_type_by_id_success(self, media_types):
        """Should return media type by ID"""
        target = media_types[0]
        
        result = get_media_type_by_id(target.id)
        
        assert result is not None
        assert result.id == target.id
        assert result.type_name == target.type_name
    
    def test_get_media_type_by_id_not_found(self, db):
        """Should return None for non-existent ID"""
        result = get_media_type_by_id(99999)
        
        assert result is None


# ============================================
# GET BY NAME SELECTOR TESTS
# ============================================

@pytest.mark.django_db
class TestGetMediaTypeByName:
    """Tests for get_media_type_by_name selector"""
    
    def test_get_media_type_by_name_success(self, media_types):
        """Should return media type by name"""
        result = get_media_type_by_name('Image')
        
        assert result is not None
        assert result.type_name == 'Image'
    
    def test_get_media_type_by_name_not_found(self, db):
        """Should return None for non-existent name"""
        result = get_media_type_by_name('NonExistent')
        
        assert result is None
    
    def test_get_media_type_by_name_case_sensitive(self, media_types):
        """Should be case-sensitive"""
        result = get_media_type_by_name('image')  # lowercase
        
        assert result is None

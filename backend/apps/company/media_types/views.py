from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny

from .models import MediaType
from .serializers import (
    MediaTypeSerializer,
    MediaTypeCreateSerializer,
    MediaTypeUpdateSerializer
)
from .selectors.media_types import list_media_types, get_media_type_by_id
from .services.media_types import (
    create_media_type,
    update_media_type,
    delete_media_type,
    MediaTypeInput
)


class MediaTypeViewSet(viewsets.GenericViewSet):
    """
    ViewSet quản lý loại media.
    
    Endpoints:
    - GET    /api/media-types/         → list (public)
    - POST   /api/media-types/         → create (admin)
    - PUT    /api/media-types/:id/     → update (admin)
    - DELETE /api/media-types/:id/     → destroy (admin)
    """
    
    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
        return list_media_types(is_active=is_active)
    
    def list(self, request):
        """
        GET /api/media-types/
        Danh sách loại media (public)
        """
        queryset = self.get_queryset()
        serializer = MediaTypeSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """
        POST /api/media-types/
        Tạo loại media mới (admin only)
        """
        serializer = MediaTypeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = MediaTypeInput(**serializer.validated_data)
            media_type = create_media_type(input_data)
            return Response(
                MediaTypeSerializer(media_type).data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None, partial=False):
        """
        PUT/PATCH /api/media-types/:id/
        Cập nhật loại media (admin only)
        """
        media_type = get_media_type_by_id(pk)
        if not media_type:
            return Response(
                {"detail": "Media type not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MediaTypeUpdateSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = MediaTypeInput(**serializer.validated_data)
            updated = update_media_type(media_type, input_data)
            return Response(MediaTypeSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    def partial_update(self, request, pk=None):
        return self.update(request, pk, partial=True)
    
    def destroy(self, request, pk=None):
        """
        DELETE /api/media-types/:id/
        Xóa loại media (admin only)
        """
        media_type = get_media_type_by_id(pk)
        if not media_type:
            return Response(
                {"detail": "Media type not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            delete_media_type(media_type)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

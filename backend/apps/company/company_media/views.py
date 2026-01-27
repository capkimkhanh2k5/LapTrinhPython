from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated

from .serializers import (
    CompanyMediaSerializer, 
    CompanyMediaCreateSerializer,
    CompanyMediaUpdateSerializer,
    CompanyMediaReorderSerializer,
    CompanyMediaBulkUploadSerializer
)
from .services.company_media import (
    upload_company_media_service,
    update_company_media_service,
    delete_company_media_service,
    reorder_company_media_service,
    bulk_upload_company_media_service,
    CompanyMediaCreateInput,
    CompanyMediaUpdateInput,
    CompanyMediaReorderInput,
    CompanyMediaBulkUploadInput
)
from .selectors import list_company_media


class CompanyMediaViewSet(viewsets.ViewSet):
    """
    ViewSet quản lý media của công ty.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def list(self, request, company_id=None):
        """Lấy danh sách media"""
        media = list_company_media(company_id=company_id)
        serializer = CompanyMediaSerializer(media, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, company_id=None):
        """Upload media đơn lẻ"""
        serializer = CompanyMediaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = CompanyMediaCreateInput(**serializer.validated_data)
            media = upload_company_media_service(
                company_id=company_id,
                user=request.user,
                data=input_data
            )
            return Response(
                CompanyMediaSerializer(media).data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, company_id=None, pk=None):
        """Cập nhật thông tin media"""
        serializer = CompanyMediaUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Pydantic v2 or strict types might complain about missing fields if we unpack dict directly
            # but Optional fields are None by default in the model definition.
            input_data = CompanyMediaUpdateInput(**serializer.validated_data)
            
            media = update_company_media_service(
                media_id=pk,
                user=request.user,
                data=input_data
            )
            return Response(CompanyMediaSerializer(media).data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, company_id=None, pk=None):
        """Xóa media"""
        try:
            delete_company_media_service(
                media_id=pk,
                user=request.user
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['patch'], url_path='reorder')
    def reorder(self, request, company_id=None):
        """Sắp xếp thứ tự media"""
        serializer = CompanyMediaReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = CompanyMediaReorderInput(reorders=serializer.validated_data['reorders'])
            reorder_company_media_service(
                company_id=company_id,
                user=request.user,
                data=input_data
            )
            return Response({"message": "Sắp xếp thành công"}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='bulk-upload')
    def bulk_upload(self, request, company_id=None):
        """Upload nhiều media cùng lúc"""
        serializer = CompanyMediaBulkUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = CompanyMediaBulkUploadInput(**serializer.validated_data)
            media_list = bulk_upload_company_media_service(
                company_id=company_id,
                user=request.user,
                data=input_data
            )
            return Response(
                CompanyMediaSerializer(media_list, many=True).data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

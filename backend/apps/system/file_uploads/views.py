from rest_framework import viewsets, status, parsers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import FileUpload
from .serializers import FileUploadSerializer
from .services.file_uploads import save_upload


class FileUploadViewSet(viewsets.ModelViewSet):
    """
        ViewSet for File Uploads
    """
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def get_queryset(self):
        """
            Người dùng chỉ thấy các file upload của mình trừ khi là admin
        """
        if self.request.user.is_staff:
            return FileUpload.objects.all()
        return FileUpload.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            upload = save_upload(
                user=request.user,
                file_obj=file_obj,
                entity_type=request.data.get('entity_type'),
                entity_id=request.data.get('entity_id'),
                is_public=request.data.get('is_public') == 'true'
            )
            return Response(FileUploadSerializer(upload).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

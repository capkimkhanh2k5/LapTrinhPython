from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from .models import SystemSetting
from .serializers import SystemSettingSerializer, SystemSettingUpdateSerializer
from .selectors.system_settings import list_settings
from .services.system_settings import update_setting


class SystemSettingViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
        ViewSet for managing System Settings
    """
    queryset = SystemSetting.objects.all()
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return SystemSettingUpdateSerializer
        return SystemSettingSerializer
        
    def get_permissions(self):
        # Chỉ dành cho admin
        if self.action in ['update', 'partial_update', 'create', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def list(self, request):
        """
            Lấy danh sách các setting
        """
        filters = request.query_params.dict()
        if not request.user.is_staff:
            filters['is_public'] = True
            
        settings = list_settings(filters=filters)
        serializer = self.get_serializer(settings, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
            Lấy thông tin của một setting
        """
        try:
            instance = self.get_object()
            if not request.user.is_staff and not instance.is_public:
                return Response(status=status.HTTP_403_FORBIDDEN)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            #TODO: Cần Kiểm tra lại 
            updated_setting = update_setting(
                user=request.user,
                setting=instance,
                value=serializer.validated_data.get('setting_value', instance.setting_value),
                description=serializer.validated_data.get('description', instance.description),
                is_public=serializer.validated_data.get('is_public', instance.is_public)
            )
            return Response(SystemSettingSerializer(updated_setting).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    @extend_schema(responses=SystemSettingSerializer(many=True))
    @action(detail=False, methods=['get'])
    def public(self, request):
        """
            Lấy danh sách các setting công khai
        """
        settings = list_settings(filters={'is_public': True})
        serializer = SystemSettingSerializer(settings, many=True)
        return Response(serializer.data)

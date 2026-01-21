from rest_framework import viewsets, mixins, status
from django.core.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from pydantic import ValidationError as PydanticValidationError

from apps.recruitment.campaigns.models import Campaign
from apps.recruitment.campaigns.serializers import (
    CampaignSerializer, CampaignDetailSerializer,
    CampaignJobAddSerializer, CampaignStatusUpdateSerializer
)
from apps.recruitment.campaigns.services.campaigns import (
    CampaignService, CampaignCreateInput, CampaignUpdateInput
)
from apps.recruitment.campaigns.selectors.campaigns import CampaignSelector
from apps.core.permissions import IsCompanyOwner

class CampaignViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsCompanyOwner]
    
    def get_queryset(self):
        # Using Selector pattern inside get_queryset for compatibility with DRF
        return CampaignSelector.list_campaigns(self.request.user.company_profile)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CampaignDetailSerializer
        if self.action == 'add_jobs':
            return CampaignJobAddSerializer
        if self.action == 'update_status':
            return CampaignStatusUpdateSerializer
        return CampaignSerializer

    @extend_schema(summary="Tạo chiến dịch tuyển dụng")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Convert serializer data to Pydantic input
            input_data = CampaignCreateInput(**serializer.validated_data)
            
            campaign = CampaignService.create_campaign(
                company=request.user.company_profile,
                data=input_data
            )
        except (ValueError, ValidationError, PydanticValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        output_serializer = CampaignSerializer(campaign)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Cập nhật chiến dịch")
    def update(self, request, *args, **kwargs):
        campaign = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = CampaignUpdateInput(**serializer.validated_data)
            
            updated_campaign = CampaignService.update_campaign(
                campaign=campaign,
                data=input_data
            )
        except (ValueError, ValidationError, PydanticValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        output_serializer = CampaignSerializer(updated_campaign)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='status')
    @extend_schema(summary="Đổi trạng thái chiến dịch")
    def update_status(self, request, pk=None):
        campaign = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = CampaignUpdateInput(status=serializer.validated_data['status'])
            
            updated_campaign = CampaignService.update_campaign(
                campaign=campaign,
                data=input_data
            )
        except (ValueError, ValidationError, PydanticValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(CampaignSerializer(updated_campaign).data)

    @action(detail=True, methods=['get'], url_path='jobs')
    @extend_schema(summary="Danh sách việc làm trong chiến dịch")
    def list_jobs(self, request, pk=None):
        campaign = self.get_object()
        jobs = campaign.jobs.all()
        # Pagination could be added here
        from apps.recruitment.jobs.serializers import JobSerializer
        return Response(JobSerializer(jobs, many=True).data)

    @action(detail=True, methods=['post'], url_path='jobs')
    @extend_schema(summary="Thêm việc làm vào chiến dịch")
    def add_jobs(self, request, pk=None):
        campaign = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        job_ids = serializer.validated_data['job_ids']
        updated_campaign = CampaignService.add_jobs(campaign, job_ids)
        
        return Response({'status': 'success', 'job_count': updated_campaign.jobs.count()})

    @action(detail=True, methods=['delete'], url_path='jobs/(?P<job_id>\d+)')
    @extend_schema(summary="Xóa việc làm khỏi chiến dịch")
    def remove_job(self, request, pk=None, job_id=None):
        campaign = self.get_object()
        CampaignService.remove_job(campaign, int(job_id))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    @extend_schema(summary="Phân tích chiến dịch")
    def analytics(self, request, pk=None):
        campaign = self.get_object()
        data = CampaignService.get_analytics(campaign)
        return Response(data.dict())

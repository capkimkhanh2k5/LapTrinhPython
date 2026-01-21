from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError as RestValidationError
from django.core.exceptions import ValidationError

from apps.recruitment.referrals.models import ReferralProgram, Referral
from apps.recruitment.referrals.serializers import ReferralProgramSerializer, ReferralSerializer
from apps.recruitment.referrals.services.referrals import ReferralService, ProgramCreateInput, ReferralCreateInput
from apps.recruitment.referrals.selectors.referrals import ReferralSelector
from apps.core.permissions import IsCompanyOwner

class ReferralProgramViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Referral Programs.
    - Company: CRUD their own programs.
    - User/Public: Only view active programs (if needed, but mainly for company management here).
    """
    serializer_class = ReferralProgramSerializer
    permission_classes = [permissions.IsAuthenticated, IsCompanyOwner]

    def get_queryset(self):
        # Only list programs belonging to the user's company
        return ReferralSelector.list_programs(self.request.user)

    def perform_create(self, serializer):
        service = ReferralService()
        data = serializer.validated_data
        
        # Pydantic conversion
        try:
            input_data = ProgramCreateInput(
                title=data['title'],
                description=data.get('description', ''),
                reward_amount=data['reward_amount'],
                currency=data.get('currency', 'VND'),
                start_date=data.get('start_date'),
                end_date=data.get('end_date'),
                job_ids=data.get('job_ids', [])
            )
            program = service.create_program(self.request.user.company_profile, input_data)
            
            serializer.instance = program
        except Exception as e:
             raise RestValidationError(str(e))

    @action(detail=True, methods=['patch'])
    def toggle(self, request, pk=None):
        program = self.get_object()
        new_status = request.data.get('status')
        if new_status not in [ReferralProgram.Status.ACTIVE, ReferralProgram.Status.PAUSED, ReferralProgram.Status.ENDED]:
             return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        program.status = new_status
        program.save()
        return Response(self.get_serializer(program).data)

class ReferralViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Referrals.
    - CREATE: Any authenticated user (referrer).
    - LIST: 
        - Company: See all referrals for their jobs.
        - User: See their own referrals.
    """
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'company_profile'): 
            #TODO: Cần kiểm tra lại logic này

            # If requesting as company, show received referrals
            # Note: A user can be both referrer and company owner. 
            # This logic needs to be clear based on endpoint or query param.
            # Assuming standard ViewSet lists "Manageable" items for Company, "Owned" items for User.
            # But here, let's distinguish via action or default behavior.
            # Default: If Company Owner, show company referrals. If Candidate, show my referrals.
            if user.role == 'employer': # Assuming role field
                 return ReferralSelector.list_company_referrals(user.company_profile)
        
        return ReferralSelector.list_my_referrals(user)

    def create(self, request, *args, **kwargs):
        service = ReferralService()
        try:
            # Pydantic Validation handled manually or via simple mapping
            data = request.data
            input_data = ReferralCreateInput(
                program_id=data.get('program_id'),
                job_id=data.get('job_id'),
                candidate_name=data.get('candidate_name'),
                candidate_email=data.get('candidate_email'),
                candidate_phone=data.get('candidate_phone'),
                notes=data.get('notes', '')
            )
            
            # Using FILE from request.FILES
            cv_file = request.FILES.get('cv_file_upload')
            if not cv_file:
                return Response({'error': 'CV File is required'}, status=status.HTTP_400_BAD_REQUEST)

            referral = service.submit_referral(request.user, input_data, cv_file)
            return Response(ReferralSerializer(referral).data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='my-referrals')
    def my_referrals(self, request):
        """Explicit endpoint for users to see their referrals"""
        qs = ReferralSelector.list_my_referrals(request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='mark-paid', permission_classes=[IsCompanyOwner])
    def mark_paid(self, request, pk=None):
        referral = self.get_object()

        #TODO: Cần kiểm tra lại logic này
        
        # Verify ownership is handled by get_queryset (if company) or manual check
        # Assuming get_queryset returns company referrals for company user
        if referral.status != Referral.Status.HIRED:
             return Response({'error': 'Referral must be HIRED before marking as PAID'}, status=status.HTTP_400_BAD_REQUEST)
        
        service = ReferralService()
        updated_referral = service.update_status(referral, Referral.Status.PAID)
        return Response(ReferralSerializer(updated_referral).data)

    @action(detail=True, methods=['patch'], url_path='update-status', permission_classes=[IsCompanyOwner])
    def update_status_action(self, request, pk=None):
        referral = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        service = ReferralService()
        updated_referral = service.update_status(referral, new_status)
        return Response(ReferralSerializer(updated_referral).data)

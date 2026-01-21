from rest_framework import serializers
from apps.recruitment.referrals.models import ReferralProgram, Referral
from apps.recruitment.jobs.serializers import JobListSerializer as JobSerializer
from apps.core.users.serializers import CustomUserSerializer as UserSerializer
from apps.company.companies.utils.cloudinary import save_raw_file

class ReferralProgramSerializer(serializers.ModelSerializer):
    jobs = serializers.PrimaryKeyRelatedField(
        many=True, 
        read_only=True
    )
    job_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = ReferralProgram
        fields = [
            'id', 'company', 'title', 'description', 
            'reward_amount', 'currency', 'status', 
            'start_date', 'end_date', 'jobs', 'job_ids',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['company', 'created_at', 'updated_at']

    def create(self, validated_data):
        job_ids = validated_data.pop('job_ids', [])
        program = super().create(validated_data)
        if job_ids:
            program.jobs.set(job_ids)
        return program

    def update(self, instance, validated_data):
        job_ids = validated_data.pop('job_ids', None)
        program = super().update(instance, validated_data)
        if job_ids is not None:
             program.jobs.set(job_ids)
        return program

class ReferralSerializer(serializers.ModelSerializer):
    program_title = serializers.CharField(source='program.title', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    referrer_name = serializers.CharField(source='referrer.name', read_only=True)
    program_id = serializers.IntegerField(write_only=True)
    job_id = serializers.IntegerField(write_only=True)
    cv_file_upload = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Referral
        fields = [
            'id', 'program', 'program_id', 'program_title',
            'job', 'job_id', 'job_title',
            'referrer', 'referrer_name',
            'candidate_name', 'candidate_email', 'candidate_phone', 
            'cv_file', 'cv_file_upload', 'status', 'referral_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['referrer', 'status', 'referral_date', 'created_at', 'updated_at', 'program', 'job', 'cv_file']

    def create(self, validated_data):
        file = validated_data.pop('cv_file_upload', None)
        program_id = validated_data.pop('program_id')
        job_id = validated_data.pop('job_id')
        
        validated_data['program_id'] = program_id
        validated_data['job_id'] = job_id
        
        if file:
            url = save_raw_file('referrals/cvs', file, 'cv')
            validated_data['cv_file'] = url
            
        return super().create(validated_data)

    def update(self, instance, validated_data):
        file = validated_data.pop('cv_file_upload', None)
        
        if file:
            url = save_raw_file('referrals/cvs', file, 'cv')
            validated_data['cv_file'] = url
            
        return super().update(instance, validated_data)


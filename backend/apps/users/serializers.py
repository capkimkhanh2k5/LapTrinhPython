from rest_framework import serializers
from .models import CustomUser, EmployerProfile, CandidateProfile

class EmployerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployerProfile
        fields = ['company_name', 'company_description', 'website', 'location']

class CandidateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = ['resume', 'skills', 'bio']

class CustomUserSerializer(serializers.ModelSerializer):
    employer_profile = EmployerProfileSerializer(read_only=True)
    candidate_profile = CandidateProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'is_employer', 'is_candidate', 'employer_profile', 'candidate_profile', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    # Logic moved to Service Layer
    # def create(self, validated_data): ...

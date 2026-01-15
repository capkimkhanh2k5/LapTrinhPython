from rest_framework import viewsets, permissions
from .models import Application
from .serializers import ApplicationSerializer

class IsEmployerOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Candidate can see their own application
        if obj.candidate == request.user:
            return True
        # Employer of the job can see applications
        if obj.job.employer == request.user:
            return True
        return False

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_employer:
            # Return applications for jobs posted by this employer
            return Application.objects.filter(job__employer=user)
        return Application.objects.filter(candidate=user)

    def perform_create(self, serializer):
        serializer.save(candidate=self.request.user)

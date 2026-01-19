from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .serializers import LanguageSerializer
from .selectors.languages import list_all_languages


class LanguageViewSet(viewsets.GenericViewSet):
    """
    ViewSet cho Language (Public API).
    
    Endpoint: GET /api/languages/
    Permission: AllowAny (public)
    """
    permission_classes = [AllowAny]
    
    def list(self, request):
        """
        GET /api/languages/
        Danh sách tất cả ngôn ngữ
        """
        queryset = list_all_languages()
        serializer = LanguageSerializer(queryset, many=True)
        return Response(serializer.data)

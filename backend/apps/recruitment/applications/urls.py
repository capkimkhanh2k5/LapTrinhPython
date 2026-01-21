from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobApplicationViewSet, ApplicationViewSet
from apps.assessment.test_results.views import ApplicationTestResultsView

# Router cho ApplicationViewSet (flat routes)
router = DefaultRouter()
router.register(r'', ApplicationViewSet, basename='applications')

# Router cho JobApplicationViewSet (nested) - used in config/urls.py
job_router = DefaultRouter()
job_router.register(r'', JobApplicationViewSet, basename='job-applications')

app_name = 'applications'

# Custom URL patterns for actions
urlpatterns = [
    # Non-pk routes must be FIRST
    path('stats/', ApplicationViewSet.as_view({'get': 'stats'}), name='application-stats'),
    path('bulk-action/', ApplicationViewSet.as_view({'post': 'bulk_action_view'}), name='application-bulk-action'),
    path('export/', ApplicationViewSet.as_view({'get': 'export'}), name='application-export'),
    # Then pk-based routes
    path('<int:pk>/status/', ApplicationViewSet.as_view({'patch': 'change_status'}), name='application-status'),
    path('<int:pk>/rating/', ApplicationViewSet.as_view({'patch': 'rate'}), name='application-rating'),
    path('<int:pk>/notes/', ApplicationViewSet.as_view({'post': 'add_notes'}), name='application-notes'),
    path('<int:pk>/history/', ApplicationViewSet.as_view({'get': 'history'}), name='application-history'),
    path('<int:pk>/shortlist/', ApplicationViewSet.as_view({'post': 'shortlist'}), name='application-shortlist'),
    path('<int:pk>/reject/', ApplicationViewSet.as_view({'post': 'reject'}), name='application-reject'),
    path('<int:pk>/offer/', ApplicationViewSet.as_view({'post': 'offer'}), name='application-offer'),
    path('<int:pk>/withdraw/', ApplicationViewSet.as_view({'post': 'applicant_withdraw'}), name='application-withdraw'),
    path('<int:pk>/interviews/', ApplicationViewSet.as_view({'get': 'list_interviews'}), name='application-interviews'),
    path('<int:application_id>/test-results/', ApplicationTestResultsView.as_view({'get': 'list'}), name='application-test-results'),
    # Standard router routes LAST
    path('', include(router.urls)),
]



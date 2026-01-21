from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from .views import CompanyViewSet
from apps.company.company_benefits.views import CompanyBenefitViewSet
from apps.social.reviews.views import CompanyReviewsView

# Main router cho companies
router = DefaultRouter()
router.register(r'', CompanyViewSet, basename='company')

# Nested router cho benefits: /api/companies/:company_pk/benefits/
companies_router = nested_routers.NestedDefaultRouter(router, r'', lookup='company')
companies_router.register(r'benefits', CompanyBenefitViewSet, basename='company-benefits')

urlpatterns = [
    path('<int:company_id>/reviews/', CompanyReviewsView.as_view({'get': 'list', 'post': 'create'}), name='company-reviews'),
    path('', include(router.urls)),
    path('', include(companies_router.urls)),
]


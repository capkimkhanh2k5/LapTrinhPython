from django.urls import path, include

urlpatterns = [
    path('companies/', include('apps.company.companies.urls')),
    path('companies/', include('apps.company.company_media.urls')),  # Register media APIs
    path('industries/', include('apps.company.industries.urls')),
    path('benefits/', include('apps.company.company_benefits.urls')),
    path('media-types/', include('apps.company.media_types.urls')),
    path('benefit-categories/', include('apps.company.benefit_categories.urls')),
]

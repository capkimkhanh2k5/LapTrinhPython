from typing import List, Optional
from django.db.models import QuerySet
from apps.recruitment.campaigns.models import Campaign
from apps.company.companies.models import Company

class CampaignSelector:
    @staticmethod
    def list_campaigns(company: Company) -> QuerySet[Campaign]:
        return Campaign.objects.filter(company=company)

    @staticmethod
    def get_campaign(pk: int, company: Company) -> Optional[Campaign]:
        return Campaign.objects.filter(pk=pk, company=company).first()

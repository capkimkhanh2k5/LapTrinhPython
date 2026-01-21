import pytest
from rest_framework import status
from django.urls import reverse
from apps.billing.models import SubscriptionPlan, CompanySubscription

@pytest.mark.django_db
class TestSubscriptionPlanViewSet:
    def test_list_plans_public(self, api_client, plan):
        url = reverse('subscription-plans-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['slug'] == plan.slug

@pytest.mark.django_db
class TestCompanySubscriptionViewSet:
    def test_get_current_subscription_none(self, authenticated_client, company):
        url = reverse('company-subscriptions-current')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_subscribe_success(self, authenticated_client, company, plan):
        url = reverse('company-subscriptions-subscribe')
        data = {'plan_id': plan.id}
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['plan']['slug'] == plan.slug
        assert response.data['status'] == 'active'

    def test_cancel_subscription(self, authenticated_client, company, plan):
        # First subscribe
        url_sub = reverse('company-subscriptions-subscribe')
        authenticated_client.post(url_sub, {'plan_id': plan.id})
        
        # Then cancel
        url_cancel = reverse('company-subscriptions-cancel')
        response = authenticated_client.post(url_cancel)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'cancelled'
        
        # Verify auto_renew is False in DB
        sub = company.subscriptions.first()
        assert sub.auto_renew is False

@pytest.mark.django_db
class TestTransactionViewSet:
    def test_list_transactions(self, authenticated_client, company, plan):
        # Subscribe creates a transaction (if price > 0, handled by service?)
        # My service creates transaction if price == 0. My fixture price is 1M.
        # But PaymentService simulation in view calls create_transaction logic if implemented.
        # Wait, View implementation had:
        # try: subscription = SubscriptionService.subscribe(..., plan)
        # It did NOT explicitly call PaymentService in View yet, checks logic.
        
        # In `views.py`:
        # # Payment Logic Simulation
        # # ...
        # subscription = SubscriptionService.subscribe(company_profile, plan)
        
        # So no transaction created for paid plan unless service does it.
        # My service `subscribe` has:
        # if plan.price == 0: Transaction.objects.create(...)
        # So for paid plan, no transaction in my current MVP implementation in `services/subscriptions.py`.
        
        # Let's update `test_services.py` or `views.py` OR create a free plan for this test.
        
        free_plan = SubscriptionPlan.objects.create(name="Free", slug="free", price=0, duration_days=30)
        
        url_sub = reverse('company-subscriptions-subscribe')
        authenticated_client.post(url_sub, {'plan_id': free_plan.id})
        
        url = reverse('transactions-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert float(response.data[0]['amount']) == 0.0

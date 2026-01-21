import pytest
from rest_framework import status
from django.urls import reverse

@pytest.mark.django_db
class TestEmailTemplateViewSet:
    def test_list_templates_admin(self, api_client, admin_user, email_template):
        api_client.force_authenticate(user=admin_user)
        url = reverse('emailtemplate-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_template_admin(self, api_client, admin_user, category):
        api_client.force_authenticate(user=admin_user)
        url = reverse('emailtemplate-list')
        data = {
            "name": "New Template",
            "slug": "new-template",
            "category_id": category.id,
            "subject": "New Subject",
            "body": "Body content"
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_access_denied_regular_user(self, api_client, regular_user):
        api_client.force_authenticate(user=regular_user)
        url = reverse('emailtemplate-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_test_send_action(self, api_client, admin_user, email_template):
        api_client.force_authenticate(user=admin_user)
        url = reverse('emailtemplate-test-send', kwargs={'slug': email_template.slug})
        data = {
            "recipient": "tester@example.com",
            "context": {"name": "Tester"}
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'sent'

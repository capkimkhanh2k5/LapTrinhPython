from django.apps import AppConfig


class SubscriptionPlansConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.billing.subscription_plans'
    label = 'billing_subscription_plans'

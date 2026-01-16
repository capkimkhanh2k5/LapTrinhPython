from django.apps import AppConfig


class PaymentTransactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.billing.payment_transactions'
    label = 'billing_payment_transactions'

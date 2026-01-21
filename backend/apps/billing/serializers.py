from rest_framework import serializers
from apps.billing.models import SubscriptionPlan, CompanySubscription, PaymentMethod, Transaction

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'slug', 'price', 'currency', 'duration_days', 'features', 'is_active', 'created_at']

class CompanySubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    
    class Meta:
        model = CompanySubscription
        fields = ['id', 'company', 'plan', 'start_date', 'end_date', 'status', 'auto_renew']

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'code', 'is_active']

class TransactionSerializer(serializers.ModelSerializer):
    payment_method = PaymentMethodSerializer(read_only=True)
    plan_name = serializers.CharField(source='company.subscription.plan.name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'company', 'payment_method', 'amount', 'currency', 'type', 'status', 'reference_code', 'description', 'created_at', 'plan_name']

class SubscribeInputSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    payment_method_code = serializers.CharField(required=False, allow_null=True)

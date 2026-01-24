from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from decimal import Decimal
import hmac, hashlib, urllib.parse
from django.conf import settings

from apps.billing.services.vnpay import VNPayService
from apps.billing.models import Transaction, CompanySubscription, PaymentMethod, SubscriptionPlan
from apps.company.companies.models import Company
from apps.company.industries.models import Industry

User = get_user_model()

class TestVNPayIntegration(APITestCase):
    
    def setUp(self):
        # Create Data
        self.user = User.objects.create_user(
            email="company@test.com",
            password="password123",
            role='employer'
        )
        self.industry = Industry.objects.create(name="Tech", slug="tech")
        self.company_profile = Company.objects.create(
            user=self.user,
            company_name="Test Company",
            slug="test-company",
            industry=self.industry
        )
        self.plan = SubscriptionPlan.objects.create(
            name="Pro Plan",
            slug="pro",
            price=Decimal("100000"),
            currency="VND",
            duration_days=30
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_vnpay_service_url_generation(self):
        """Test URL generation logic matches VNPay requirements"""
        url = VNPayService.get_payment_url(
            order_id="TEST_REF",
            amount=Decimal("100000"),
            order_desc="Test Order",
            ip_addr="127.0.0.1"
        )
        self.assertIn("vnp_SecureHash=", url)
        self.assertIn("vnp_Amount=10000000", url) # x100 check

    def test_subscribe_api_auto_creates_payment_method(self):
        """Test that subscribe API auto-seeds 'vnpay' payment method"""
        
        # Ensure no payment method exists initially
        PaymentMethod.objects.all().delete()
        
        url = reverse('company-subscriptions-subscribe')
        data = {'plan_id': self.plan.id}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_url', response.data)
        
        # Verify PaymentMethod was created
        pm = PaymentMethod.objects.filter(code='vnpay').first()
        self.assertIsNotNone(pm)
        self.assertEqual(pm.name, 'VNPay Gateway')
        
        # Verify Transaction Created
        txn = Transaction.objects.first()
        self.assertEqual(txn.status, Transaction.Status.PENDING)
        self.assertEqual(txn.payment_method, pm)

    def test_payment_return_flow_success(self):
        """Test full cyclic flow: Subscribe -> Get URL -> Return -> Activate"""
        
        # 1. Subscribe
        url = reverse('company-subscriptions-subscribe')
        response = self.client.post(url, {'plan_id': self.plan.id})
        txn_ref = response.data['transaction_ref']
        
        # 2. Simulate User Paying on VNPay -> Validating Return URL
        params = {
            'vnp_Amount': '10000000',
            'vnp_BankCode': 'NCB',
            'vnp_CardType': 'ATM',
            'vnp_OrderInfo': 'Subscribe',
            'vnp_PayDate': '20260101000000',
            'vnp_ResponseCode': '00',
            'vnp_TmnCode': 'EMBIL7EU',
            'vnp_TransactionNo': '12345678',
            'vnp_TxnRef': txn_ref,
        }
        
        # Generate Signature
        sorted_params = sorted(params.items())
        query_str = urllib.parse.urlencode(sorted_params)
        
        # Use settings (handling mock if needed)
        secret = getattr(settings, 'VNP_HASH_SECRET', 'FP2480JF752TUW5PZWV8MSHCE4FAWB2V')
        
        secure_hash = hmac.new(
            secret.encode('utf-8'),
            query_str.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        params['vnp_SecureHash'] = secure_hash
        
        # 3. Call Return API
        return_url = reverse('company-subscriptions-payment-return')
        response = self.client.get(return_url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Payment Successful")
        
        # 4. Verify DB State
        txn = Transaction.objects.get(reference_code=txn_ref)
        self.assertEqual(txn.status, Transaction.Status.COMPLETED)
        self.assertEqual(txn.vnp_TransactionNo, '12345678')
        
        # Verify Subscription Activated
        sub_id = txn.description.split('|')[1].split(':')[1]
        sub = CompanySubscription.objects.get(id=sub_id)
        self.assertEqual(sub.status, CompanySubscription.Status.ACTIVE)

from django.db import transaction
from apps.billing.models import Transaction, PaymentMethod

class PaymentService:
    @staticmethod
    def process_payment(company, amount, payment_method: PaymentMethod, description: str = "") -> Transaction:

        #TODO: Cần xem lại logic này, tích hợp thanh toán bằng VN PAY hoặc các gateway khác
        
        # Simulate payment processing
        # In reality, this would integrate with Stripe/PayPal APIs
        
        transaction = Transaction.objects.create(
            company=company,
            payment_method=payment_method,
            amount=amount,
            status=Transaction.Status.PENDING,
            description=description
        )
        
        # Simulate Success
        transaction.status = Transaction.Status.COMPLETED
        import uuid
        transaction.reference_code = str(uuid.uuid4())
        transaction.save()
        
        return transaction

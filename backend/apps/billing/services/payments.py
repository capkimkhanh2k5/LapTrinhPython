from django.db import transaction
from apps.billing.models import Transaction, PaymentMethod
from apps.billing.services.vnpay import VNPayService

class PaymentService:
    @staticmethod
    def process_payment(company, amount, payment_method: PaymentMethod, description: str = "", ip_addr: str = "127.0.0.1") -> tuple[Transaction, str]:
        """
        Initiate payment process.
        Returns:
            (Transaction, payment_url)
        """
        
        # 1. Create Pending Transaction
        with transaction.atomic():
            txn = Transaction.objects.create(
                company=company,
                payment_method=payment_method,
                amount=amount,
                status=Transaction.Status.PENDING,
                description=description,
                ip_address=ip_addr
            )
            
            # Generate unique reference code based on ID
            txn.reference_code = f"ORDER_{txn.id}_{company.id}"
            txn.save()
        
        # 2. Generate Payment URL (VNPay)
        # TODO: Handle other gateways if needed
        # TODO: Có thể thêm các cổng khác ngoài VN Pay
        
        payment_url = VNPayService.get_payment_url(
            order_id=txn.reference_code,
            amount=amount,
            order_desc=f"{description[:50]}...",
            ip_addr=ip_addr
        )
        
        return txn, payment_url

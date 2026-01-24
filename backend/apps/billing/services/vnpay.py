import hashlib
import hmac
import urllib.parse
from datetime import datetime
from django.conf import settings

class VNPayService:
    """
    Service for handling VNPay payment gateway integration.
    """
    
    @staticmethod
    def get_payment_url(order_id, amount, order_desc, ip_addr):
        """
        Generate VNPay payment URL.
        
        Args:
            order_id (str): Unique transaction reference.
            amount (Decimal): Amount in VND.
            order_desc (str): Description of the order.
            ip_addr (str): Client IP address.
            
        Returns:
            str: Full redirect URL to VNPay.
        """
        
        # 1. Prepare Base Params
        vnp_params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': settings.VNP_TMN_CODE,
            'vnp_Amount': int(amount * 100),  # Required: Amount * 100
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': str(order_id),
            'vnp_OrderInfo': order_desc,
            'vnp_OrderType': 'other', # or 'billpayment'
            # 'vnp_Locale': 'vn', # Optional, defaults to vn
            'vnp_ReturnUrl': settings.VNP_RETURN_URL,
            'vnp_IpAddr': ip_addr,
            'vnp_CreateDate': datetime.now().strftime('%Y%m%d%H%M%S'),
        }
        
        # 2. Sort Params by Key (Alphabetical)
        inputData = sorted(vnp_params.items())
        
        # 3. Create Query String & Raw Hash Data
        hasData = ''
        seq = 0
        for key, val in inputData:
            if seq == 1:
                hasData = hasData + "&" + str(key) + '=' + urllib.parse.quote_plus(str(val))
            else:
                seq = 1
                hasData = str(key) + '=' + urllib.parse.quote_plus(str(val))
        
        # 4. Generate Checksum (HMAC-SHA512)
        vnp_HashSecret = settings.VNP_HASH_SECRET
        vnp_SecureHash = hmac.new(
            vnp_HashSecret.encode('utf-8'), 
            hasData.encode('utf-8'), 
            hashlib.sha512
        ).hexdigest()
        
        # 5. Build Final URL
        payment_url = f"{settings.VNP_URL}?{hasData}&vnp_SecureHash={vnp_SecureHash}"
        
        return payment_url

    @staticmethod
    def validate_payment(query_params):
        """
        Validate VNPay response checksum.
        
        Args:
            query_params (dict): Request query parameters (request.GET)
            
        Returns:
            bool: True if checksum is valid, False otherwise.
        """
        vnp_SecureHash = query_params.get('vnp_SecureHash')
        if not vnp_SecureHash:
            return False
            
        # Filter and Sort params
        inputData = {}
        for key, val in query_params.items():
            if key.startswith('vnp_') and key not in ['vnp_SecureHash', 'vnp_SecureHashType']:
                inputData[key] = val
        
        inputData = sorted(inputData.items())
        
        # Recreate Hash Data
        hasData = ''
        seq = 0
        for key, val in inputData:
            if seq == 1:
                hasData = hasData + "&" + str(key) + '=' + urllib.parse.quote_plus(str(val))
            else:
                seq = 1
                hasData = str(key) + '=' + urllib.parse.quote_plus(str(val))
        
        # Verify
        vnp_HashSecret = settings.VNP_HASH_SECRET
        secureHash = hmac.new(
            vnp_HashSecret.encode('utf-8'), 
            hasData.encode('utf-8'), 
            hashlib.sha512
        ).hexdigest()
        
        return secureHash == vnp_SecureHash

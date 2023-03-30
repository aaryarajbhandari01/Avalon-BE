# from rest_framework.response import requests
from django.conf import settings
# import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status



# KHALTI_API_KEY = settings.KHALTI_API_KEY
KHALTI_API_KEY = 'test_secret_key_8f4896b93ad44015a75085470b5dd0f9'
KHALTI_API_URL = "https://a.khalti.com/api/v2/epayment/initiate/"


def initiate_payment(amount, purchase_order_id, purchase_order_name):
    data = {
        "return_url": "https://example.com/payment/",
        "website_url": "https://example.com/",
        "amount": amount,
        "purchase_order_id": purchase_order_id,
        "purchase_order_name": purchase_order_name,
    }
    headers = {
        'Authorization': f'Key {KHALTI_API_KEY}',
    }
    response = requests.post(KHALTI_API_URL, data=data, headers=headers)
    print(response)
    return response.json()

class PaymentInitiateView(APIView):
    def post(self, request):
        payment_id = request.data.get('payment_id')
        amount = request.data.get('amount')
        data = {
            'amount': amount,
            'token': payment_id,
        }
        headers = {
            'Authorization': f'Key {KHALTI_API_KEY}',
        }
        response = requests.post(KHALTI_API_URL, data=data, headers=headers)
        if response.status_code == 200:
            return Response({'url': response.json().get('redirect_url')})
        return Response({'message': 'Payment initiation failed'}, status=status.HTTP_400_BAD_REQUEST)
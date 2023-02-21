# import requests
from django.conf import settings

KHALTI_API_KEY = settings.KHALTI_API_KEY
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
    return response.json()

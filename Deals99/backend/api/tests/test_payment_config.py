from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class PaymentConfigAPITestCase(TestCase):
    def test_payment_config_returns_keys(self):
        client = APIClient()
        response = client.get(reverse('payment_config'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stripe_publishable_key', response.data)
        self.assertIn('razorpay_key_id', response.data)
        self.assertIn('stripe_enabled', response.data)

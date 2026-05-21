"""API tests for payment intent create/verify endpoints."""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.models import Order, Payment

User = get_user_model()


class PaymentIntentAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='payuser',
            email='payuser@example.com',
            password='testpass123',
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('499.00'),
            shipping_address='123 Test St',
            payment_method='stripe',
        )
        self.client.force_authenticate(user=self.user)

    def test_create_intent_requires_order_id(self):
        response = self.client.post(reverse('payment_create_intent'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('order_id', response.data['error'])

    def test_create_intent_order_not_found(self):
        response = self.client.post(
            reverse('payment_create_intent'),
            {'order_id': 99999, 'payment_method': 'stripe'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.views.PaymentProcessor.create_payment_intent')
    def test_create_intent_success(self, mock_create):
        mock_create.return_value = {
            'success': True,
            'client_secret': 'sec_test',
            'payment_intent_id': 'pi_test_abc',
            'amount': 499.0,
            'currency': 'usd',
        }
        response = self.client.post(
            reverse('payment_create_intent'),
            {'order_id': self.order.id, 'payment_method': 'stripe'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['client_secret'], 'sec_test')
        self.assertTrue(Payment.objects.filter(payment_id='pi_test_abc', order=self.order).exists())

    @patch('api.views.PaymentProcessor.create_payment_intent')
    def test_create_intent_provider_unconfigured(self, mock_create):
        mock_create.return_value = {'success': False, 'error': 'Payment system not configured'}
        response = self.client.post(
            reverse('payment_create_intent'),
            {'order_id': self.order.id, 'payment_method': 'stripe'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch('api.views.PaymentProcessor.verify_payment')
    def test_verify_payment_success(self, mock_verify):
        Payment.objects.create(
            order=self.order,
            payment_id='pi_verify_1',
            payment_method='stripe',
            amount=self.order.total_amount,
            status='pending',
        )
        mock_verify.return_value = {
            'success': True,
            'status': 'completed',
            'payment_id': 'pi_verify_1',
            'amount': Decimal('499.00'),
        }
        response = self.client.post(
            reverse('payment_verify'),
            {'payment_id': 'pi_verify_1', 'payment_method': 'stripe'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'completed')

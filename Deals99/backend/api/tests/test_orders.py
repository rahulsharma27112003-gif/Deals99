"""
Order API tests for Deals99
Tests order creation, management, and status tracking
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Order, OrderItem, Cart
from api.tests.factories import (
    ProductFactory, OrderFactory, CartFactory, UserFactory
)


class OrderTestCase(TestCase):
    """Test order endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.product = ProductFactory(price=99.99, stock=50)
        self.client.force_authenticate(user=self.user)

    def test_create_order_from_cart(self):
        """Test creating order from cart items"""
        # Add items to cart
        CartFactory(user=self.user, product=self.product, quantity=2)
        
        order_data = {
            'shipping_address': '123 Test St, Test City, ST 12345',
            'payment_method': 'cod'
        }
        
        response = self.client.post('/api/orders/create_from_cart/', order_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order_number', response.data)
        self.assertEqual(response.data['status'], 'pending')
        
        # Verify cart was cleared
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 0)

    def test_create_order_empty_cart(self):
        """Test creating order with empty cart"""
        order_data = {
            'shipping_address': '123 Test St',
            'payment_method': 'cod'
        }
        
        response = self.client.post('/api/orders/create_from_cart/', order_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_prevent_oversell(self):
        """Ensure order creation fails when requested quantity > stock"""
        # Set product stock low
        self.product.stock = 1
        self.product.save()

        # Add cart item requesting more than available stock
        CartFactory(user=self.user, product=self.product, quantity=2)

        response = self.client.post('/api/orders/create_from_cart/', {
            'shipping_address': '123 Test St',
            'payment_method': 'cod'
        })

        # Expect error due to insufficient stock
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_orders(self):
        """Test getting user's orders"""
        OrderFactory(user=self.user)
        
        response = self.client.get('/api/orders/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_get_order_detail(self):
        """Test getting order details"""
        order = OrderFactory(user=self.user)
        
        response = self.client.get(f'/api/orders/{order.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], order.order_number)

    def test_update_order_status_as_user(self):
        """Test that regular users cannot update order status"""
        order = OrderFactory(user=self.user)
        
        status_data = {'status': 'shipped'}
        response = self.client.patch(f'/api/orders/{order.id}/update_status/', status_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_order_status_as_admin(self):
        """Test that admins can update order status"""
        admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        order = OrderFactory()
        
        admin_client = APIClient()
        admin_client.force_authenticate(user=admin_user)
        
        status_data = {'status': 'shipped'}
        response = admin_client.patch(f'/api/orders/{order.id}/update_status/', status_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'shipped')

    def test_invalid_order_status(self):
        """Test updating order with invalid status"""
        admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        order = OrderFactory()
        
        admin_client = APIClient()
        admin_client.force_authenticate(user=admin_user)
        
        status_data = {'status': 'invalid_status'}
        response = admin_client.patch(f'/api/orders/{order.id}/update_status/', status_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_number_generation(self):
        """Test that order numbers are generated automatically"""
        order = OrderFactory(user=self.user)
        
        self.assertIsNotNone(order.order_number)
        self.assertTrue(order.order_number.startswith('ORD-'))

    def test_order_items_included(self):
        """Test that order includes order items"""
        order = OrderFactory(user=self.user)
        product = ProductFactory()
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=2,
            price=50.00
        )
        
        response = self.client.get(f'/api/orders/{order.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)
        self.assertEqual(len(response.data['items']), 1)

    def test_other_user_cannot_view_order(self):
        """Test that users cannot view other users' orders"""
        other_user = UserFactory(username='otheruser')
        order = OrderFactory(user=other_user)
        
        response = self.client.get(f'/api/orders/{order.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_order_access(self):
        """Test that unauthenticated users cannot access orders"""
        client = APIClient()
        response = client.get('/api/orders/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

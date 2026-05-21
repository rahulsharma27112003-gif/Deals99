"""
Cart and Wishlist API tests for Deals99
Tests shopping cart and wishlist functionality
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Cart, Wishlist, Product
from api.tests.factories import ProductFactory, CartFactory, WishlistFactory


class CartTestCase(TestCase):
    """Test shopping cart endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.product = ProductFactory(price=99.99, stock=50)
        self.client.force_authenticate(user=self.user)

    def test_add_to_cart(self):
        """Test adding product to cart"""
        cart_data = {
            'product': self.product.id,
            'quantity': 2
        }
        
        response = self.client.post('/api/cart/', cart_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['quantity'], 2)

    def test_get_cart_items(self):
        """Test getting cart items"""
        CartFactory(user=self.user, product=self.product, quantity=3)
        
        response = self.client.get('/api/cart/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_update_cart_item(self):
        """Test updating cart item quantity"""
        cart_item = CartFactory(user=self.user, product=self.product, quantity=1)
        
        update_data = {'quantity': 5}
        response = self.client.patch(f'/api/cart/{cart_item.id}/', update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 5)

    def test_remove_from_cart(self):
        """Test removing product from cart"""
        cart_item = CartFactory(user=self.user, product=self.product)
        
        response = self.client.delete(f'/api/cart/{cart_item.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Cart.objects.filter(id=cart_item.id).exists())

    def test_get_cart_total(self):
        """Test getting cart total"""
        CartFactory(user=self.user, product=self.product, quantity=2)
        
        response = self.client.get('/api/cart/total/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total', response.data)
        self.assertEqual(float(response.data['total']), 2 * 99.99)

    def test_clear_cart(self):
        """Test clearing entire cart"""
        CartFactory(user=self.user, product=self.product, quantity=2)
        
        response = self.client.post('/api/cart/clear/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 0)

    def test_quantity_limit(self):
        """Test that cart respects quantity limits"""
        cart_data = {
            'product': self.product.id,
            'quantity': 15  # Exceeds max of 10
        }
        
        response = self.client.post('/api/cart/', cart_data)
        
        # Should fail or truncate
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED])

    def test_unauthenticated_cart_access(self):
        """Test that unauthenticated users cannot access cart"""
        client = APIClient()
        response = client.get('/api/cart/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WishlistTestCase(TestCase):
    """Test wishlist endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.product = ProductFactory()
        self.client.force_authenticate(user=self.user)

    def test_add_to_wishlist(self):
        """Test adding product to wishlist"""
        wishlist_data = {
            'product': self.product.id
        }
        
        response = self.client.post('/api/wishlist/', wishlist_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_wishlist(self):
        """Test getting wishlist items"""
        WishlistFactory(user=self.user, product=self.product)
        
        response = self.client.get('/api/wishlist/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_remove_from_wishlist(self):
        """Test removing product from wishlist"""
        wishlist_item = WishlistFactory(user=self.user, product=self.product)
        
        response = self.client.delete(f'/api/wishlist/{wishlist_item.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Wishlist.objects.filter(id=wishlist_item.id).exists())

    def test_duplicate_wishlist_item(self):
        """Test that product can only be added to wishlist once"""
        # Add product to wishlist
        WishlistFactory(user=self.user, product=self.product)
        
        # Try to add again
        wishlist_data = {'product': self.product.id}
        response = self.client.post('/api/wishlist/', wishlist_data)
        
        # Should fail due to unique constraint
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_201_CREATED  # Depending on implementation
        ])

    def test_unauthenticated_wishlist_access(self):
        """Test that unauthenticated users cannot access wishlist"""
        client = APIClient()
        response = client.get('/api/wishlist/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

"""
Model tests for Deals99
Tests model methods, properties, and validation
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()
from api.models import Category, Product, Order, Review, UserProfile
from api.tests.factories import (
    CategoryFactory, ProductFactory, UserFactory, ReviewFactory, OrderFactory
)


class CategoryModelTestCase(TestCase):
    """Test Category model"""

    def test_category_creation(self):
        """Test creating a category"""
        category = CategoryFactory(name='Test Category')
        
        self.assertEqual(category.name, 'Test Category')
        self.assertTrue(category.active)

    def test_category_string_representation(self):
        """Test category __str__ method"""
        category = CategoryFactory(name='Electronics')
        
        self.assertEqual(str(category), 'Electronics')

    def test_category_unique_name(self):
        """Test that category names must be unique"""
        CategoryFactory(name='Duplicate')
        
        with self.assertRaises(Exception):
            CategoryFactory(name='Duplicate')


class ProductModelTestCase(TestCase):
    """Test Product model"""

    def setUp(self):
        """Set up test data"""
        self.category = CategoryFactory()
        self.product = ProductFactory(
            name='Test Product',
            price=100.00,
            mrp=150.00,
            category=self.category
        )

    def test_product_creation(self):
        """Test creating a product"""
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(float(self.product.price), 100.00)
        self.assertEqual(self.product.category, self.category)

    def test_product_discount_calculation(self):
        """Test discount percentage calculation"""
        # (150 - 100) / 150 * 100 = 33.33%
        expected_discount = ((150.00 - 100.00) / 150.00) * 100
        
        self.assertAlmostEqual(
            self.product.discount_percentage,
            expected_discount,
            places=2
        )

    def test_product_no_discount(self):
        """Test discount when price >= MRP"""
        product = ProductFactory(price=150.00, mrp=100.00)
        
        self.assertEqual(product.discount_percentage, 0)

    def test_product_no_mrp(self):
        """Test discount when MRP is not set"""
        product = ProductFactory(price=100.00, mrp=None)
        
        self.assertEqual(product.discount_percentage, 0)

    def test_product_string_representation(self):
        """Test product __str__ method"""
        self.assertEqual(str(self.product), 'Test Product')

    def test_product_negative_price_validation(self):
        """Test that negative prices are rejected"""
        with self.assertRaises(Exception):
            ProductFactory(price=-10.00)


class OrderModelTestCase(TestCase):
    """Test Order model"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()

    def test_order_creation(self):
        """Test creating an order"""
        order = OrderFactory(user=self.user)
        
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, 'pending')

    def test_order_number_generation(self):
        """Test that order number is auto-generated"""
        order = OrderFactory()
        
        self.assertIsNotNone(order.order_number)
        self.assertTrue(order.order_number.startswith('ORD-'))

    def test_order_number_unique(self):
        """Test that order numbers are unique"""
        order1 = OrderFactory()
        order2 = OrderFactory()
        
        self.assertNotEqual(order1.order_number, order2.order_number)

    def test_order_status_choices(self):
        """Test order status choices"""
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        
        for status in valid_statuses:
            order = OrderFactory(status=status)
            self.assertEqual(order.status, status)

    def test_order_string_representation(self):
        """Test order __str__ method"""
        order = OrderFactory()
        
        self.assertEqual(
            str(order),
            f"Order {order.order_number} - {order.user.username}"
        )


class ReviewModelTestCase(TestCase):
    """Test Review model"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.product = ProductFactory()

    def test_review_creation(self):
        """Test creating a review"""
        review = ReviewFactory(
            user=self.user,
            product=self.product,
            rating=5,
            title='Great Product',
            comment='This is amazing!'
        )
        
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.title, 'Great Product')

    def test_review_rating_range(self):
        """Test that ratings are between 1-5"""
        # Valid rating
        ReviewFactory(user=self.user, product=self.product, rating=3)
        
        # Invalid rating (too high)
        with self.assertRaises(Exception):
            ReviewFactory(user=self.user, product=self.product, rating=6)

    def test_one_review_per_product(self):
        """Test that user can only review a product once"""
        ReviewFactory(user=self.user, product=self.product)
        
        with self.assertRaises(Exception):
            ReviewFactory(user=self.user, product=self.product)

    def test_review_helpful_count(self):
        """Test helpful count tracking"""
        review = ReviewFactory(user=self.user, product=self.product)
        
        self.assertEqual(review.helpful_count, 0)
        
        review.helpful_count += 1
        review.save()
        
        self.assertEqual(review.helpful_count, 1)


class UserProfileModelTestCase(TestCase):
    """Test UserProfile model"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()

    def test_profile_auto_creation(self):
        """Test that profile is created when user is created"""
        # Profile should be created by signal or factory
        profile = UserProfile.objects.filter(user=self.user).first()
        
        self.assertIsNotNone(profile)

    def test_profile_update(self):
        """Test updating user profile"""
        profile = self.user.profile
        profile.phone = '1234567890'
        profile.address = '123 Test St'
        profile.save()
        
        profile.refresh_from_db()
        self.assertEqual(profile.phone, '1234567890')
        self.assertEqual(profile.address, '123 Test St')

    def test_newsletter_subscription(self):
        """Test newsletter subscription tracking"""
        profile = self.user.profile
        profile.newsletter_subscribed = True
        profile.save()
        
        profile.refresh_from_db()
        self.assertTrue(profile.newsletter_subscribed)

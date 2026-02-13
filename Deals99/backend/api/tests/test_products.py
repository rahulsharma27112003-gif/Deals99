"""
Product API tests for Deals99
Tests product listing, filtering, and search functionality
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Category, Subcategory, Product, ProductImage
from api.tests.factories import (
    CategoryFactory, SubcategoryFactory, ProductFactory, ProductImageFactory
)


class ProductListingTestCase(TestCase):
    """Test product listing and filtering"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test categories
        self.category1 = CategoryFactory(name='Electronics')
        self.category2 = CategoryFactory(name='Fashion')
        
        # Create test subcategories
        self.subcat1 = SubcategoryFactory(name='Phones', parent_category=self.category1)
        self.subcat2 = SubcategoryFactory(name='Shirts', parent_category=self.category2)
        
        # Create test products
        self.product1 = ProductFactory(
            name='Test Phone',
            category=self.category1,
            subcategory=self.subcat1,
            price=499.99,
            mrp=699.99,
            stock=50,
            active=True,
            featured=True
        )
        self.product2 = ProductFactory(
            name='Test Shirt',
            category=self.category2,
            subcategory=self.subcat2,
            price=29.99,
            mrp=49.99,
            stock=100,
            active=True,
            featured=False
        )
        self.product3 = ProductFactory(
            name='Inactive Product',
            category=self.category1,
            stock=10,
            active=False
        )

    def test_list_all_products(self):
        """Test listing all active products"""
        response = self.client.get('/api/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include pagination
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 2)

    def test_filter_by_category(self):
        """Test filtering products by category"""
        response = self.client.get(f'/api/products/?category={self.category1.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Should only include products from category1
        for product in response.data['results']:
            self.assertEqual(product['category'], self.category1.id)

    def test_filter_by_price_range(self):
        """Test filtering products by price range"""
        response = self.client.get('/api/products/?min_price=100&max_price=500')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that products fall within price range
        for product in response.data['results']:
            self.assertGreaterEqual(float(product['price']), 100)
            self.assertLessEqual(float(product['price']), 500)

    def test_get_featured_products(self):
        """Test getting featured products"""
        response = self.client.get('/api/products/featured/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data if 'results' in response.data else response.data)

    def test_get_products_with_discounts(self):
        """Test getting products with discounts (deals)"""
        response = self.client.get('/api/products/deals/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_products(self):
        """Test searching products by name"""
        response = self.client.get('/api/products/?search=Phone')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_get_product_detail(self):
        """Test getting individual product details"""
        response = self.client.get(f'/api/products/{self.product1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Phone')
        self.assertEqual(response.data['price'], '499.99')

    def test_product_discount_calculation(self):
        """Test that discount percentage is calculated correctly"""
        response = self.client.get(f'/api/products/{self.product1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Discount should be (699.99 - 499.99) / 699.99 * 100
        expected_discount = ((699.99 - 499.99) / 699.99) * 100
        self.assertAlmostEqual(
            float(response.data['discount_percentage']), 
            expected_discount, 
            places=1
        )

    def test_product_images(self):
        """Test that product includes images"""
        # Add an image to product
        ProductImageFactory(product=self.product1, is_primary=True)
        
        response = self.client.get(f'/api/products/{self.product1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('images', response.data)
        self.assertGreater(len(response.data['images']), 0)


class CategoryTestCase(TestCase):
    """Test category endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.category = CategoryFactory(name='Test Category')
        SubcategoryFactory(parent_category=self.category, name='Subcat 1')
        SubcategoryFactory(parent_category=self.category, name='Subcat 2')

    def test_list_categories(self):
        """Test listing all categories"""
        response = self.client.get('/api/categories/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_get_category_detail(self):
        """Test getting category details"""
        response = self.client.get(f'/api/categories/{self.category.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Category')

    def test_get_subcategories(self):
        """Test getting subcategories for a category"""
        response = self.client.get(f'/api/categories/{self.category.id}/subcategories/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

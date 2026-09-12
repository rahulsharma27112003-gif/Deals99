#!/usr/bin/env python
"""
Setup script for Deals99 Backend
Run this script to initialize the Django project with sample data
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model
from api.models import Category, Subcategory, Product, ProductImage, UserProfile

User = get_user_model()

def setup_database():
    """Initialize database and create sample data"""
    print("Setting up database...")
    
    # Create or update superuser credentials
    superadmin_email = 'superadmin@example.com'
    superadmin_password = 'Admin12345'
    superadmin_username = 'superadmin'

    superadmin = User.objects.filter(email=superadmin_email).first()
    if superadmin:
        superadmin.username = superadmin_username
        superadmin.first_name = 'Super'
        superadmin.last_name = 'Admin'
        superadmin.is_staff = True
        superadmin.is_superuser = True
        superadmin.set_password(superadmin_password)
        superadmin.save()
        print(f"✓ Updated existing admin user (email: {superadmin_email})")
    else:
        User.objects.create_superuser(
            email=superadmin_email,
            password=superadmin_password,
            username=superadmin_username,
            first_name='Super',
            last_name='Admin'
        )
        print(f"✓ Created admin user (username: {superadmin_username}, password: {superadmin_password})")
    
    # Create sample categories
    categories_data = [
        {'name': 'Electronics', 'description': 'Electronic devices and accessories', 'icon': 'fas fa-laptop'},
        {'name': 'Fashion', 'description': 'Clothing and fashion accessories', 'icon': 'fas fa-tshirt'},
        {'name': 'Gifts', 'description': 'Gift items and personalized products', 'icon': 'fas fa-gift'},
        {'name': 'Home & Living', 'description': 'Home decor and lifestyle products', 'icon': 'fas fa-home'},
        {'name': 'Sports', 'description': 'Sports equipment and fitness gear', 'icon': 'fas fa-dumbbell'},
    ]
    
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        if created:
            print(f"✓ Created category: {category.name}")
    
    # Create sample subcategories
    subcategories_data = [
        {'name': 'Mobile Phones', 'parent_category': 'Electronics', 'description': 'Smartphones and mobile devices', 'icon': 'fas fa-mobile-alt'},
        {'name': 'Laptops', 'parent_category': 'Electronics', 'description': 'Laptops and computers', 'icon': 'fas fa-laptop'},
        {'name': 'Accessories', 'parent_category': 'Electronics', 'description': 'Electronic accessories', 'icon': 'fas fa-headphones'},
        {'name': "Men's Clothing", 'parent_category': 'Fashion', 'description': 'Clothing for men', 'icon': 'fas fa-male'},
        {'name': "Women's Clothing", 'parent_category': 'Fashion', 'description': 'Clothing for women', 'icon': 'fas fa-female'},
        {'name': 'Birthday Gifts', 'parent_category': 'Gifts', 'description': 'Gifts for birthdays', 'icon': 'fas fa-birthday-cake'},
        {'name': 'Anniversary Gifts', 'parent_category': 'Gifts', 'description': 'Gifts for anniversaries', 'icon': 'fas fa-heart'},
    ]
    
    for subcat_data in subcategories_data:
        parent_category = Category.objects.get(name=subcat_data['parent_category'])
        subcategory, created = Subcategory.objects.get_or_create(
            name=subcat_data['name'],
            parent_category=parent_category,
            defaults=subcat_data
        )
        if created:
            print(f"✓ Created subcategory: {subcategory.name}")
    
    # Create sample products
    products_data = [
        {
            'name': 'Wireless Headphones',
            'description': 'High-quality wireless headphones with noise cancellation',
            'price': 1299.00,
            'mrp': 1999.00,
            'category': 'Electronics',
            'subcategory': 'Accessories',
            'stock': 50,
            'featured': True
        },
        {
            'name': 'Smart Watch',
            'description': 'Feature-rich smartwatch with health tracking',
            'price': 2499.00,
            'mrp': 3999.00,
            'category': 'Electronics',
            'subcategory': 'Accessories',
            'stock': 30,
            'featured': True
        },
        {
            'name': 'Custom T-Shirt',
            'description': 'Personalized t-shirt with your design',
            'price': 499.00,
            'mrp': 799.00,
            'category': 'Fashion',
            'subcategory': "Men's Clothing",
            'stock': 100,
            'featured': True
        },
        {
            'name': 'Phone Case',
            'description': 'Premium phone case with protection',
            'price': 99.00,
            'mrp': 299.00,
            'category': 'Electronics',
            'subcategory': 'Accessories',
            'stock': 200
        },
        {
            'name': 'Keychain',
            'description': 'Personalized keychain for your keys',
            'price': 99.00,
            'mrp': 199.00,
            'category': 'Gifts',
            'subcategory': 'Birthday Gifts',
            'stock': 150
        },
    ]
    
    for product_data in products_data:
        category = Category.objects.get(name=product_data['category'])
        subcategory = Subcategory.objects.get(
            name=product_data['subcategory'],
            parent_category=category
        )
        
        product, created = Product.objects.get_or_create(
            name=product_data['name'],
            defaults={
                'description': product_data['description'],
                'price': product_data['price'],
                'mrp': product_data['mrp'],
                'category': category,
                'subcategory': subcategory,
                'stock': product_data['stock'],
                'featured': product_data.get('featured', False)
            }
        )
        if created:
            print(f"✓ Created product: {product.name}")
    
    print("\n✓ Database setup completed successfully!")
    print("\nAdmin credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nAPI endpoints available at: http://localhost:8000/api/")

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deals99_backend.config.settings.dev')
    django.setup()
    
    # Run migrations
    print("Running migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Setup database with sample data
    setup_database()

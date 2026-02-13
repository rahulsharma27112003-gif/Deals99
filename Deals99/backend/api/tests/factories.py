"""
Test factories for creating test data using Factory Boy
"""

import factory
from django.contrib.auth import get_user_model

User = get_user_model()
from api.models import (
    Category, Subcategory, Product, ProductImage, UserProfile,
    Cart, Wishlist, Order, OrderItem, Review, Banner, Payment
)


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users"""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.django.Password('testpass123')
    is_active = True


class UserProfileFactory(factory.django.DjangoModelFactory):
    """Factory for creating user profiles"""
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    phone = factory.Faker('phone_number')
    address = factory.Faker('address')
    gender = factory.Faker('random_element', elements=['male', 'female', 'other'])
    newsletter_subscribed = True


class CategoryFactory(factory.django.DjangoModelFactory):
    """Factory for creating categories"""
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Category {n}')
    description = factory.Faker('text')
    icon = 'fas fa-tag'
    active = True


class SubcategoryFactory(factory.django.DjangoModelFactory):
    """Factory for creating subcategories"""
    class Meta:
        model = Subcategory

    name = factory.Sequence(lambda n: f'Subcategory {n}')
    parent_category = factory.SubFactory(CategoryFactory)
    description = factory.Faker('text')
    icon = 'fas fa-tag'
    active = True


class ProductFactory(factory.django.DjangoModelFactory):
    """Factory for creating products"""
    class Meta:
        model = Product

    name = factory.Faker('word')
    description = factory.Faker('text')
    price = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    mrp = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    category = factory.SubFactory(CategoryFactory)
    subcategory = factory.SubFactory(SubcategoryFactory)
    stock = factory.Faker('random_int', min=0, max=100)
    active = True
    featured = False


class ProductImageFactory(factory.django.DjangoModelFactory):
    """Factory for creating product images"""
    class Meta:
        model = ProductImage

    product = factory.SubFactory(ProductFactory)
    image = factory.django.ImageField()
    alt_text = factory.Faker('word')
    is_primary = False


class CartFactory(factory.django.DjangoModelFactory):
    """Factory for creating cart items"""
    class Meta:
        model = Cart

    user = factory.SubFactory(UserFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker('random_int', min=1, max=5)


class WishlistFactory(factory.django.DjangoModelFactory):
    """Factory for creating wishlist items"""
    class Meta:
        model = Wishlist

    user = factory.SubFactory(UserFactory)
    product = factory.SubFactory(ProductFactory)


class OrderFactory(factory.django.DjangoModelFactory):
    """Factory for creating orders"""
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = 'pending'
    total_amount = factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
    shipping_address = factory.Faker('address')
    payment_method = 'cod'
    payment_status = 'pending'


class OrderItemFactory(factory.django.DjangoModelFactory):
    """Factory for creating order items"""
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker('random_int', min=1, max=5)
    price = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)


class ReviewFactory(factory.django.DjangoModelFactory):
    """Factory for creating reviews"""
    class Meta:
        model = Review

    user = factory.SubFactory(UserFactory)
    product = factory.SubFactory(ProductFactory)
    rating = factory.Faker('random_int', min=1, max=5)
    title = factory.Faker('sentence')
    comment = factory.Faker('text')
    helpful_count = 0


class BannerFactory(factory.django.DjangoModelFactory):
    """Factory for creating banners"""
    class Meta:
        model = Banner

    title = factory.Faker('sentence')
    description = factory.Faker('text')
    image = factory.django.ImageField()
    link_url = factory.Faker('url')
    active = True
    order = factory.Sequence(lambda n: n)


class PaymentFactory(factory.django.DjangoModelFactory):
    """Factory for creating payments"""
    class Meta:
        model = Payment

    order = factory.SubFactory(OrderFactory)
    payment_id = factory.Faker('uuid4')
    payment_method = 'stripe'
    status = 'pending'
    amount = factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
    currency = 'USD'
    transaction_id = factory.Faker('uuid4')

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()
from .models import (
    Category, Subcategory, Product, ProductImage, UserProfile,
    Cart, Wishlist, Order, OrderItem, Payment, Review, Banner
)


class CategorySerializer(serializers.ModelSerializer):
    subcategories_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon', 'active', 'subcategories_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_subcategories_count(self, obj):
        return obj.subcategories.filter(active=True).count()


class SubcategorySerializer(serializers.ModelSerializer):
    parent_category_name = serializers.CharField(source='parent_category.name', read_only=True)
    
    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'parent_category', 'parent_category_name', 'description', 'icon', 'active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'created_at']
        read_only_fields = ['created_at']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    discount_percentage = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'mrp', 'category', 'category_name',
            'subcategory', 'subcategory_name', 'stock', 'active', 'featured',
            'discount_percentage', 'average_rating', 'reviews_count',
            'images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / len(reviews), 2)
        return 0

    def get_reviews_count(self, obj):
        return obj.reviews.count()


class ProductListSerializer(serializers.ModelSerializer):
    """Simplified serializer for product lists"""
    category = serializers.PrimaryKeyRelatedField(read_only=True)
    subcategory = serializers.PrimaryKeyRelatedField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'mrp', 'category', 'subcategory',
            'category_name', 'subcategory_name',
            'stock', 'active', 'featured', 'discount_percentage', 'average_rating',
            'primary_image', 'created_at'
        ]

    def get_primary_image(self, obj):
        primary_img = obj.images.filter(is_primary=True).first()
        if primary_img:
            return self.context['request'].build_absolute_uri(primary_img.image.url)
        first_img = obj.images.first()
        if first_img:
            return self.context['request'].build_absolute_uri(first_img.image.url)
        return None

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / len(reviews), 2)
        return 0


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'phone',
            'address',
            'date_of_birth',
            'gender',
            'newsletter_subscribed',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'profile',
            'role',
            'is_email_verified',
            'is_staff',
            'is_superuser',
        ]
        read_only_fields = ['is_staff', 'is_superuser', 'role', 'is_email_verified']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def create(self, validated_data):
        # Create using the custom user manager
        return User.objects.create_user(**validated_data)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    phone = serializers.CharField(max_length=15, required=False)
    address = serializers.CharField(required=False)
    date_of_birth = serializers.DateField(required=False)
    gender = serializers.ChoiceField(choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], required=False)
    newsletter_subscribed = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm',
                  'phone', 'address', 'date_of_birth', 'gender', 'newsletter_subscribed']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        profile_data = {
            'phone': validated_data.pop('phone', ''),
            'address': validated_data.pop('address', ''),
            'date_of_birth': validated_data.pop('date_of_birth', None),
            'gender': validated_data.pop('gender', ''),
            'newsletter_subscribed': validated_data.pop('newsletter_subscribed', False)
        }
        
        user = User.objects.create_user(**validated_data)
        # Update the auto-created profile with the provided data
        profile = user.profile
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.save()
        return user


# --- Password reset serializers ---
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs


class CartSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_id', 'created_at']
        read_only_fields = ['created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price', 'total_price']
        read_only_fields = ['total_price']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializes a Payment record (read-only for Order payloads)."""
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'payment_method', 'status', 'amount', 'currency',
            'transaction_id', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'payment_id', 'status', 'created_at', 'completed_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    payment = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'user_name', 'user_email', 'status',
            'total_amount', 'shipping_address', 'payment_method', 'payment_status',
            'payment', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'order_number',
            'created_at',
            'updated_at',
            'status',
            'payment_status',
            'user',
            'total_amount',
        ]

    def get_payment(self, obj):
        """Return the latest Payment for the order (or None)."""
        latest = obj.payments.order_by('-created_at').first()
        if not latest:
            return None
        return PaymentSerializer(latest, context=self.context).data


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'user_name', 'user_username', 'product', 'rating',
            'title', 'comment', 'helpful_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'helpful_count', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BannerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Banner
        fields = ['id', 'title', 'description', 'image', 'image_url', 'link_url', 'active', 'order', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

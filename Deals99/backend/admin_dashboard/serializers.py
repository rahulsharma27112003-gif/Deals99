from django.contrib.auth import get_user_model

User = get_user_model()
from rest_framework import serializers

from api.models import Product, Order, OrderItem, Payment, Refund


class AdminUserSerializer(serializers.ModelSerializer):
    # Prefer `user.role` (new custom user); fall back to legacy profile.role when present
    role = serializers.SerializerMethodField()
    order_count = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'is_staff',
            'is_superuser',
            'role',
            'order_count',
            'total_spent',
            'date_joined',
        ]

    def get_role(self, obj):
        role = getattr(obj, 'role', getattr(getattr(obj, 'profile', None), 'role', None))
        if role is None:
            return 'CUSTOMER'
        return str(role).replace('-', '_').replace(' ', '_').upper()


class AdminProductSummarySerializer(serializers.ModelSerializer):
    total_quantity_sold = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'price',
            'stock',
            'active',
            'featured',
            'total_quantity_sold',
            'total_revenue',
        ]


class AdminLowStockProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'stock',
            'active',
            'featured',
        ]


class AdminRefundSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='payment.order.order_number', read_only=True)
    user = serializers.CharField(source='payment.order.user.username', read_only=True)

    class Meta:
        model = Refund
        fields = [
            'id',
            'refund_id',
            'payment',
            'order_number',
            'user',
            'amount',
            'status',
            'reason',
            'created_at',
            'updated_at',
        ]


class AdminOrderStatusUpdateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    status = serializers.CharField(max_length=20)


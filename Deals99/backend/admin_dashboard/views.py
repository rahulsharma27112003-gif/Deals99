from django.contrib.auth import get_user_model

User = get_user_model()
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from api.models import Product, Order, OrderItem, Refund
from api.permissions import IsAdminOrManager
from api.services.dashboard import get_overview_statistics, get_revenue_time_buckets
from api.services.orders import update_order_status
from .serializers import (
    AdminUserSerializer,
    AdminProductSummarySerializer,
    AdminLowStockProductSerializer,
    AdminRefundSerializer,
    AdminOrderStatusUpdateSerializer,
)


def success_response(data, message=None, status_code=200):
    payload = {'success': True, 'data': data}
    if message:
        payload['message'] = message
    return Response(payload, status=status_code)


def error_response(message, status_code=400, errors=None):
    payload = {'success': False, 'message': message}
    if errors is not None:
        payload['errors'] = errors
    return Response(payload, status=status_code)


class AdminDashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get(self, request):
        """
        High-level KPIs for the admin dashboard:
        users, orders, revenue, pending orders, catalog stats.
        """
        stats = get_overview_statistics()
        return success_response(stats)


class RevenueAggregationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get(self, request):
        """
        Daily, weekly and monthly revenue aggregation based on completed orders.
        """
        buckets = get_revenue_time_buckets()
        return success_response(buckets)


class TopProductsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get(self, request):
        """
        Top selling products by quantity and revenue.
        """
        limit = int(request.query_params.get('limit', 10))
        order_items = (
            OrderItem.objects
            .select_related('product')
            .filter(order__payment_status='completed')
            .values('product_id', 'product__name', 'product__price', 'product__stock', 'product__active', 'product__featured')
            .annotate(
                total_quantity_sold=Coalesce(Sum('quantity'), 0),
                total_revenue=Coalesce(Sum('price'), 0),
            )
            .order_by('-total_quantity_sold')[:limit]
        )

        # Map annotated values back into lightweight objects for serialization
        products_map = {row['product_id']: row for row in order_items}
        products = Product.objects.filter(id__in=products_map.keys())

        # Attach annotations to product instances
        for product in products:
            row = products_map[product.id]
            product.total_quantity_sold = row['total_quantity_sold']
            product.total_revenue = row['total_revenue']

        serializer = AdminProductSummarySerializer(products, many=True)
        return success_response(serializer.data)


class LowStockProductsView(ListAPIView):
    """
    Products that are running low on stock.
    """

    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = AdminLowStockProductSerializer

    def get_queryset(self):
        threshold = int(self.request.query_params.get('threshold', 10))
        return Product.objects.filter(stock__lt=threshold, active=True).order_by('stock')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)


class AdminUsersView(ListAPIView):
    """
    List users with aggregated order statistics, ready for consumption by a modern frontend.
    """

    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        return (
            User.objects
            .annotate(
                order_count=Count('orders', distinct=True),
                total_spent=Coalesce(
                    Sum('orders__total_amount', filter=Q(orders__payment_status='completed')),
                    0,
                ),
            )
            .order_by('-date_joined')
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)


class AdminRefundsView(ListAPIView):
    """
    View and audit refund records.
    """

    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = AdminRefundSerializer

    def get_queryset(self):
        return (
            Refund.objects
            .select_related('payment', 'payment__order', 'payment__order__user')
            .order_by('-created_at')
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)


class AdminOrderStatusUpdateView(APIView):
    """
    Dedicated endpoint to update order status from the admin dashboard.
    """

    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def post(self, request):
        serializer = AdminOrderStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Invalid payload", status_code=400, errors=serializer.errors)

        order_id = serializer.validated_data['order_id']
        new_status = serializer.validated_data['status']

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return error_response("Order not found", status_code=404)

        try:
            updated_order = update_order_status(order, new_status)
        except ValueError:
            return error_response("Invalid status", status_code=400)

        return success_response(
            {
                'order_id': updated_order.id,
                'order_number': updated_order.order_number,
                'status': updated_order.status,
            },
            message="Order status updated successfully",
        )


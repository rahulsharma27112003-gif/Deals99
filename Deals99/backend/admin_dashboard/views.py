from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

User = get_user_model()

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
import csv
from django.http import HttpResponse
from django.utils.encoding import smart_str
from io import TextIOWrapper


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
                    Value(0),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
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


class AdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        serializer = AdminUserSerializer(user)
        return success_response(serializer.data)

    def patch(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        serializer = AdminUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, message='User updated successfully')
        return error_response('Invalid payload', status_code=400, errors=serializer.errors)

    def delete(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        if user.pk == request.user.pk:
            return error_response('Cannot delete the currently logged in admin user', status_code=400)
        user.delete()
        return success_response({}, message='User deleted successfully')


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


class AdminProductExportCSVView(APIView):
    """
    Export products as CSV for admin consumption.
    """

    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get(self, request):
        fields = ['id', 'name', 'category', 'price', 'stock', 'active', 'featured', 'mrp', 'subcategory', 'description']
        products = Product.objects.select_related('category', 'subcategory').all()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=products-export.csv'
        writer = csv.writer(response)
        writer.writerow(fields)
        for p in products:
            writer.writerow([
                p.id,
                smart_str(p.name),
                smart_str(p.category.name if p.category else ''),
                str(p.price),
                p.stock,
                int(bool(p.active)),
                int(bool(p.featured)),
                str(p.mrp) if p.mrp is not None else '',
                smart_str(p.subcategory.name if p.subcategory else ''),
                smart_str(p.description or ''),
            ])
        return response


class AdminProductImportCSVView(APIView):
    """
    Import CSV file to create or update products. CSV must include header with at least 'name' and 'price'.
    If 'id' is provided rows will update existing products, otherwise new products will be created.
    Unknown categories will be created automatically.
    """

    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return error_response('No file uploaded', status_code=400)

        # Wrap uploaded file to text stream for csv.DictReader
        try:
            csv_file = TextIOWrapper(file_obj.file, encoding=request.encoding or 'utf-8')
        except Exception:
            csv_file = TextIOWrapper(file_obj.file, encoding='utf-8', errors='replace')

        reader = csv.DictReader(csv_file)
        created = 0
        updated = 0
        errors = []

        from api.models import Category, Subcategory

        for i, row in enumerate(reader, start=1):
            try:
                # Normalize keys and strip values
                row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                prod_id = row.get('id') or row.get('product_id')
                name = row.get('name')
                price = row.get('price')
                stock = row.get('stock') or 0
                active = row.get('active')
                featured = row.get('featured')
                mrp = row.get('mrp')
                category_name = row.get('category') or row.get('category_name')
                subcategory_name = row.get('subcategory')
                description = row.get('description') or ''

                if not name or price in (None, ''):
                    errors.append({'row': i, 'error': 'Missing required name or price'})
                    continue

                # Resolve or create category
                category_obj = None
                if category_name:
                    category_obj, _ = Category.objects.get_or_create(name=category_name)

                subcat_obj = None
                if subcategory_name and category_obj:
                    subcat_obj, _ = Subcategory.objects.get_or_create(name=subcategory_name, parent_category=category_obj)

                if prod_id:
                    # Update existing
                    try:
                        prod = Product.objects.get(pk=int(prod_id))
                        prod.name = name
                        prod.price = float(price)
                        prod.stock = int(stock or 0)
                        prod.active = bool(int(active)) if active not in (None, '') else prod.active
                        prod.featured = bool(int(featured)) if featured not in (None, '') else prod.featured
                        prod.mrp = float(mrp) if mrp not in (None, '') else prod.mrp
                        if category_obj:
                            prod.category = category_obj
                        if subcat_obj:
                            prod.subcategory = subcat_obj
                        prod.description = description
                        prod.save()
                        updated += 1
                    except Product.DoesNotExist:
                        errors.append({'row': i, 'error': f'Product id {prod_id} not found'})
                else:
                    # Create new product (require category)
                    if not category_obj:
                        category_obj, _ = Category.objects.get_or_create(name='Uncategorized')
                    prod = Product.objects.create(
                        name=name,
                        price=float(price),
                        stock=int(stock or 0),
                        active=bool(int(active)) if active not in (None, '') else True,
                        featured=bool(int(featured)) if featured not in (None, '') else False,
                        mrp=float(mrp) if mrp not in (None, '') else None,
                        category=category_obj,
                        subcategory=subcat_obj,
                        description=description,
                    )
                    created += 1
            except Exception as e:
                errors.append({'row': i, 'error': str(e)})

        return success_response({'created': created, 'updated': updated, 'errors': errors}, message='CSV import completed')


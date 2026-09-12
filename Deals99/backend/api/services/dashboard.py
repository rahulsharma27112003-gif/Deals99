from django.contrib.auth import get_user_model

User = get_user_model()
from django.db.models import Count, DecimalField, Sum, Value
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, Coalesce

from api.models import Category, Subcategory, Product, Order, Review


from django.core.cache import cache


def get_overview_statistics() -> dict:
    """
    Core statistics for the admin overview dashboard. Cached for a short TTL to
    reduce DB load for dashboard consumers.
    """
    cache_key = 'admin:overview:stats'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    completed_revenue = (
        Order.objects.filter(payment_status='completed')
        .aggregate(total=Sum('total_amount'))
        .get('total')
        or 0
    )

    data = {
        'total_products': Product.objects.count(),
        'active_products': Product.objects.filter(active=True).count(),
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'total_users': User.objects.count(),
        'total_reviews': Review.objects.count(),
        'low_stock_products': Product.objects.filter(stock__lt=10).count(),
        'total_categories': Category.objects.count(),
        'total_subcategories': Subcategory.objects.count(),
        'total_revenue': completed_revenue,
    }

    cache.set(cache_key, data, timeout=300)  # 5 minutes
    return data


def get_revenue_time_buckets() -> dict:
    """
    Returns daily, weekly, and monthly revenue aggregations based on completed orders.
    Cached for dashboard performance.
    """
    cache_key = 'admin:revenue:buckets'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    base_qs = Order.objects.filter(payment_status='completed')

    daily = (
        base_qs.annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2)))
        .order_by('-day')
    )

    weekly = (
        base_qs.annotate(week=TruncWeek('created_at'))
        .values('week')
        .annotate(total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2)))
        .order_by('-week')
    )

    monthly = (
        base_qs.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2)))
        .order_by('-month')
    )

    result = {
        'daily': list(daily),
        'weekly': list(weekly),
        'monthly': list(monthly),
    }

    cache.set(cache_key, result, timeout=300)
    return result


from django.urls import path

from .views import (
    AdminDashboardOverviewView,
    RevenueAggregationView,
    TopProductsView,
    LowStockProductsView,
    AdminUsersView,
    AdminRefundsView,
    AdminOrderStatusUpdateView,
)


urlpatterns = [
    path('dashboard/', AdminDashboardOverviewView.as_view(), name='admin-dashboard-overview'),
    path('revenue/', RevenueAggregationView.as_view(), name='admin-revenue'),
    path('top-products/', TopProductsView.as_view(), name='admin-top-products'),
    path('low-stock/', LowStockProductsView.as_view(), name='admin-low-stock'),
    path('users/', AdminUsersView.as_view(), name='admin-users'),
    path('refunds/', AdminRefundsView.as_view(), name='admin-refunds'),
    path('order-status-update/', AdminOrderStatusUpdateView.as_view(), name='admin-order-status-update'),
]


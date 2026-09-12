from django.urls import path

from .views import (
    AdminDashboardOverviewView,
    RevenueAggregationView,
    TopProductsView,
    LowStockProductsView,
    AdminUsersView,
    AdminUserDetailView,
    AdminRefundsView,
    AdminOrderStatusUpdateView,
    AdminProductExportCSVView,
    AdminProductImportCSVView,
)


urlpatterns = [
    path('dashboard/', AdminDashboardOverviewView.as_view(), name='admin-dashboard-overview'),
    path('revenue/', RevenueAggregationView.as_view(), name='admin-revenue'),
    path('top-products/', TopProductsView.as_view(), name='admin-top-products'),
    path('low-stock/', LowStockProductsView.as_view(), name='admin-low-stock'),
    path('users/', AdminUsersView.as_view(), name='admin-users'),
    path('users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('refunds/', AdminRefundsView.as_view(), name='admin-refunds'),
    path('order-status-update/', AdminOrderStatusUpdateView.as_view(), name='admin-order-status-update'),
    path('products/export-csv/', AdminProductExportCSVView.as_view(), name='admin-products-export-csv'),
    path('products/import-csv/', AdminProductImportCSVView.as_view(), name='admin-products-import-csv'),
]


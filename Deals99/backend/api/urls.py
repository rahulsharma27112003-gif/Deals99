from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthView, RegisterView, VerifyEmailView, RequestPasswordResetView, PasswordResetConfirmView,
    TokenRefreshFromCookieView, GetCSRFTokenView, LogoutView, AuthMeView,
    CategoryViewSet, SubcategoryViewSet,
    ProductViewSet, CartViewSet, WishlistViewSet, OrderViewSet,
    ReviewViewSet, BannerViewSet, UserProfileViewSet,     DashboardView,
    HealthCheckView,
    PaymentCreateIntentView,
    PaymentVerifyView,
    PaymentConfigView,
)
from .webhooks import StripeWebhookView, RazorpayWebhookView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'subcategories', SubcategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'banners', BannerViewSet, basename='banners')
router.register(r'profile', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('auth/login/', AuthView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/me/', AuthMeView.as_view(), name='auth_me'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('auth/password-reset/request/', RequestPasswordResetView.as_view(), name='password_reset_request'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/refresh/', TokenRefreshFromCookieView.as_view(), name='token_refresh_cookie'),
    path('auth/csrf/', GetCSRFTokenView.as_view(), name='get_csrf_token'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    path('payments/config/', PaymentConfigView.as_view(), name='payment_config'),
    path('payments/create-intent/', PaymentCreateIntentView.as_view(), name='payment_create_intent'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment_verify'),
    # Payment webhook endpoints (verify signatures; create PaymentAudit entries)
    path('payments/stripe-webhook/', StripeWebhookView.as_view(), name='stripe_webhook'),
    path('payments/razorpay-webhook/', RazorpayWebhookView.as_view(), name='razorpay_webhook'),

    path('health/', HealthCheckView.as_view(), name='health'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('', include(router.urls)),
]

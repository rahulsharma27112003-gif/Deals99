from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.middleware.csrf import get_token
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from rest_framework.throttling import ScopedRateThrottle
from django.db import IntegrityError

User = get_user_model()
from django.db.models import Q, Avg, Count, F
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Category,
    Subcategory,
    Product,
    ProductImage,
    UserProfile,
    Cart,
    Wishlist,
    Order,
    OrderItem,
    Payment,
    Review,
    Banner,
)
from .serializers import (
    CategorySerializer,
    SubcategorySerializer,
    ProductSerializer,
    ProductListSerializer,
    UserSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    CartSerializer,
    WishlistSerializer,
    OrderSerializer,
    OrderItemSerializer,
    ReviewSerializer,
    BannerSerializer,
)
from .permissions import IsAdminOrManager, IsStaffOrAbove
from .services.orders import create_order_from_cart, EmptyCartError, update_order_status
from .services.dashboard import get_overview_statistics
from .payments import PaymentProcessor


class AuthView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        """Login endpoint"""
        identifier = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')

        if not identifier or not password:
            return Response({'error': 'Username/email and password required'}, status=status.HTTP_400_BAD_REQUEST)

        # Try to find the user record first so we can enforce lockout policies and
        # provide consistent error messages without revealing account existence.
        user = None
        try:
            # email is the primary identifier for the new User model; try both
            user = User.objects.filter(email__iexact=identifier).first() or User.objects.filter(username=identifier).first()
        except Exception:
            user = None

        # If user is locked, deny immediately
        if user and getattr(user, 'is_locked', False):
            return Response({'error': 'Account temporarily locked due to multiple failed login attempts. Try again later.'}, status=status.HTTP_423_LOCKED)

        # Authenticate using configured authentication backend (username field is email for custom user)
        auth_user = authenticate(username=identifier, password=password)
        if auth_user and auth_user.is_active:
            # Successful login: reset failed attempts
            try:
                auth_user.reset_failed_attempts()
            except Exception:
                pass

            refresh = RefreshToken.for_user(auth_user)
            response = Response({'access': str(refresh.access_token), 'user': UserSerializer(auth_user).data})

            cookie_max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
            response.set_cookie(
                key='refresh',
                value=str(refresh),
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=cookie_max_age,
                path='/'
            )
            get_token(request)
            return response

        # Authentication failed: increment failed attempts when user exists
        if user:
            try:
                limit = getattr(settings, 'AUTH_MAX_FAILED_LOGIN_ATTEMPTS', 5)
                lock_minutes = getattr(settings, 'AUTH_LOCK_MINUTES', 15)
                user.increment_failed_attempts(limit=limit, lock_minutes=lock_minutes)
            except Exception:
                pass

        # Standardized error response to avoid account enumeration
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        """Registration endpoint with email verification.

        New users are created `is_active=False` until they verify their email.
        An email verification token is sent and the API returns a friendly message.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Development: immediate activation + JWT for local/testing UX
            if settings.DEBUG:
                user.is_active = True
                if hasattr(user, 'is_email_verified'):
                    user.is_email_verified = True
                user.save()
                refresh = RefreshToken.for_user(user)
                response = Response({
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data,
                }, status=status.HTTP_201_CREATED)
                cookie_max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
                response.set_cookie(
                    key='refresh',
                    value=str(refresh),
                    httponly=True,
                    secure=not settings.DEBUG,
                    samesite='Lax',
                    max_age=cookie_max_age,
                    path='/',
                )
                get_token(request)
                try:
                    from .notifications import NotificationTrigger
                    NotificationTrigger.on_user_registered(user)
                except Exception:
                    pass
                return response

            # Production: require email verification before login
            try:
                user.is_active = False
                if hasattr(user, 'is_email_verified'):
                    user.is_email_verified = False
                user.save()
            except Exception:
                pass

            from utils.tokens import make_email_verification_token
            from .notifications import EmailNotificationService

            token = make_email_verification_token(user)
            EmailNotificationService.send_verification_email(user, token)

            return Response(
                {'detail': 'Registration successful. Verify your email before logging in.'},
                status=status.HTTP_201_CREATED,
            )

        errors = serializer.errors
        non_field_errors = errors.get('non_field_errors')
        if non_field_errors:
            return Response({'error': non_field_errors[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'detail': 'Token required'}, status=status.HTTP_400_BAD_REQUEST)

        from utils.tokens import verify_email_verification_token

        data = verify_email_verification_token(token)
        if not data:
            return Response({'detail': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=data['user_id'])
        except User.DoesNotExist:
            return Response({'detail': 'User not found for token'}, status=status.HTTP_404_NOT_FOUND)

        # mark as verified and active
        user.is_active = True
        if hasattr(user, 'is_email_verified'):
            user.is_email_verified = True
        user.save()

        return Response({'detail': 'Email verified. You can now login.'})


class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from .serializers import PasswordResetRequestSerializer
        from utils.tokens import make_password_reset_token
        from .notifications import EmailNotificationService

        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Do not reveal whether the email exists; respond with 200 OK
            return Response({'detail': 'If an account with that email exists, a reset email has been sent.'})

        token = make_password_reset_token(user)
        EmailNotificationService.send_password_reset(user, token)
        return Response({'detail': 'If an account with that email exists, a reset email has been sent.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from .serializers import PasswordResetConfirmSerializer
        from utils.tokens import verify_password_reset_token

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        pw = serializer.validated_data['password']

        data = verify_password_reset_token(token)
        if not data:
            return Response({'detail': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=data['user_id'])
        except User.DoesNotExist:
            return Response({'detail': 'User not found for token'}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(pw)
        user.save()
        return Response({'detail': 'Password reset successful.'})


class TokenRefreshFromCookieView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Refresh access token using HttpOnly refresh cookie with rotation support."""
        refresh_token = request.COOKIES.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token not provided.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Validate existing refresh token
            refresh = RefreshToken(refresh_token)
        except Exception:
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Rotate refresh token: blacklist old one (if enabled) and issue a new pair
        try:
            refresh.blacklist()
        except AttributeError:
            # token_blacklist app may not be enabled; ignore
            pass
        user_id = refresh.get('user_id')
        if not user_id:
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found for this token.'}, status=status.HTTP_401_UNAUTHORIZED)

        new_refresh = RefreshToken.for_user(user)
        new_access = str(new_refresh.access_token)

        response = Response({'access': new_access})
        cookie_max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
        response.set_cookie(
            key='refresh',
            value=str(new_refresh),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=cookie_max_age,
            path='/',
        )
        return response


class GetCSRFTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Ensure a CSRF cookie is set so frontend can read it and include in requests."""
        token = get_token(request)
        return Response({'csrfToken': token})


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Logout: blacklist refresh token (if present) and clear cookie."""
        refresh_token = request.COOKIES.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                # blacklist if blacklist app is enabled
                try:
                    token.blacklist()
                except AttributeError:
                    # token_blacklist app may not be available
                    pass
            except Exception:
                pass

        response = Response({'detail': 'Logged out'})
        # delete cookie by setting empty value and max_age=0
        response.delete_cookie('refresh', path='/')
        return response


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        """Get subcategories for a category"""
        category = self.get_object()
        subcategories = category.subcategories.filter(active=True)
        serializer = SubcategorySerializer(subcategories, many=True)
        return Response(serializer.data)


class SubcategoryViewSet(viewsets.ModelViewSet):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent_category', 'active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'subcategory').prefetch_related('images', 'reviews')
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsStaffOrAbove()]
        return [AllowAny()]
    filterset_fields = ['category', 'subcategory', 'active', 'featured']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']

    def list(self, request, *args, **kwargs):
        # Cache product listing responses (querystring-aware) for short TTL
        from django.core.cache import cache
        cache_key = f"products:list:{request.get_full_path()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        response = super().list(request, *args, **kwargs)
        # Cache only successful responses
        if response.status_code == 200:
            cache.set(cache_key, response.data, timeout=60)
        return response

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
            
        return queryset

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        products = self.get_queryset().filter(featured=True, active=True)
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def deals(self, request):
        """Get products with discounts"""
        products = self.get_queryset().filter(active=True, mrp__isnull=False).exclude(mrp__lte=F('price'))
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get product reviews"""
        product = self.get_object()
        reviews = product.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        """Add a review for the product"""
        product = self.get_object()
        serializer = ReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).select_related('product', 'product__category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Support both `product` and `product_id` in the request body for backwards compatibility.
        """
        data = request.data.copy()
        if 'product' in data and 'product_id' not in data:
            data['product_id'] = data['product']

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'])
    def total(self, request):
        """Get cart total"""
        cart_items = self.get_queryset()
        total = sum(item.total_price for item in cart_items)
        return Response({'total': total})

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear cart"""
        self.get_queryset().delete()
        return Response({'message': 'Cart cleared'})


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product', 'product__category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Support both `product` and `product_id` in the request body for
        backwards compatibility and handle duplicate wishlist entries gracefully.
        """
        data = request.data.copy()
        if 'product' in data and 'product_id' not in data:
            data['product_id'] = data['product']

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return Response(
                {'error': 'This product is already in the wishlist.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all().prefetch_related('items', 'items__product')
        return Order.objects.filter(user=self.request.user).prefetch_related('items', 'items__product')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        """
        Use stricter permissions for admin-only actions.
        """
        if self.action in ['update_status']:
            # Match original behavior: any staff user can update order status.
            return [IsAuthenticated(), IsStaffOrAbove()]
        return super().get_permissions()

    @action(detail=False, methods=['post'])
    def create_from_cart(self, request):
        """Create order from cart items"""
        shipping_address = request.data.get('shipping_address', '')
        payment_method = request.data.get('payment_method', 'cod')

        try:
            result = create_order_from_cart(
                user=request.user,
                shipping_address=shipping_address,
                payment_method=payment_method,
            )
        except EmptyCartError:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderSerializer(result.order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update order status (admin only)"""
        order = self.get_object()
        new_status = request.data.get('status')
        try:
            updated_order = update_order_status(order, new_status)
        except ValueError:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = OrderSerializer(updated_order)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark review as helpful"""
        review = self.get_object()
        review.helpful_count += 1
        review.save()
        return Response({'helpful_count': review.helpful_count})


class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.filter(active=True)
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]
    ordering = ['order', '-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Get or update current user profile (merged with User account fields)."""
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        def profile_payload():
            data = UserProfileSerializer(profile).data
            user = request.user
            data.update({
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
            })
            return data

        if request.method == 'GET':
            return Response(profile_payload())

        data = request.data.copy()
        if 'birth_date' in data and 'date_of_birth' not in data:
            data['date_of_birth'] = data.pop('birth_date')

        user = request.user
        user_updated = False
        for field in ('first_name', 'last_name', 'email'):
            if field in data:
                setattr(user, field, data.pop(field))
                user_updated = True
        if user_updated:
            user.save(update_fields=['first_name', 'last_name', 'email'])

        serializer = UserProfileSerializer(profile, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(profile_payload())
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentConfigView(APIView):
    """Public payment provider configuration for client-side checkout."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({
            'stripe_publishable_key': getattr(settings, 'STRIPE_PUBLIC_KEY', '') or '',
            'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', '') or '',
            'stripe_enabled': bool(getattr(settings, 'STRIPE_SECRET_KEY', '')),
            'razorpay_enabled': bool(
                getattr(settings, 'RAZORPAY_KEY_ID', '') and getattr(settings, 'RAZORPAY_KEY_SECRET', '')
            ),
        })


class PaymentCreateIntentView(APIView):
    """Create a Stripe PaymentIntent or Razorpay order for an existing order."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        payment_method = request.data.get('payment_method', 'stripe')
        if not order_id:
            return Response({'error': 'order_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(pk=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if payment_method not in ('stripe', 'razorpay'):
            return Response(
                {'error': 'payment_method must be stripe or razorpay'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = PaymentProcessor.create_payment_intent(order, payment_method)
        if not result.get('success'):
            return Response(
                {'success': False, 'error': result.get('error', 'Payment setup failed')},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        payment_id = result.get('payment_intent_id') or result.get('razorpay_order_id')
        currency = (result.get('currency') or ('INR' if payment_method == 'razorpay' else 'USD')).upper()
        Payment.objects.update_or_create(
            payment_id=payment_id,
            defaults={
                'order': order,
                'payment_method': payment_method,
                'amount': order.total_amount,
                'currency': currency,
                'status': 'pending',
                'response_data': {k: v for k, v in result.items() if k != 'success'},
            },
        )

        payload = {k: v for k, v in result.items() if k != 'success'}
        payload['success'] = True
        payload['order_id'] = order.id
        payload['order_number'] = order.order_number
        return Response(payload, status=status.HTTP_201_CREATED)


class PaymentVerifyView(APIView):
    """Verify an online payment after client-side completion."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get('payment_id')
        payment_method = request.data.get('payment_method', 'stripe')
        if not payment_id:
            return Response({'error': 'payment_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if payment_method not in ('stripe', 'razorpay'):
            return Response(
                {'error': 'payment_method must be stripe or razorpay'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = PaymentProcessor.verify_payment(payment_id, payment_method)
        payment = Payment.objects.filter(payment_id=payment_id, order__user=request.user).first()
        if payment and result.get('success'):
            new_status = result.get('status', 'completed')
            if new_status == 'completed':
                payment.mark_as_completed()
                payment.order.payment_status = 'completed'
                payment.order.save(update_fields=['payment_status', 'updated_at'])
            elif new_status == 'processing':
                payment.status = 'processing'
                payment.save(update_fields=['status', 'updated_at'])

        if not result.get('success'):
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)


class HealthCheckView(APIView):
    """Liveness/readiness probe for load balancers and Docker."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        from django.db import connection
        db_ok = True
        try:
            connection.ensure_connection()
        except Exception:
            db_ok = False
        return Response({
            'status': 'ok' if db_ok else 'degraded',
            'service': 'deals99-api',
            'database': 'ok' if db_ok else 'unavailable',
        }, status=status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE)


class DashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Admin dashboard statistics"""
        stats = get_overview_statistics()
        return Response(stats)

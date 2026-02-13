from django.contrib import admin
import logging

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
    Review,
    Banner,
    Payment,
    Refund,
)


logger = logging.getLogger('api')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_category', 'active', 'created_at']
    list_filter = ['parent_category', 'active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['parent_category', 'name']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'active', 'featured', 'created_at']
    list_filter = ['category', 'active', 'featured', 'created_at']
    search_fields = ['name', 'description']
    inlines = [ProductImageInline]
    ordering = ['-created_at']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    ordering = ['-created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'newsletter_subscribed', 'created_at']
    list_filter = ['role', 'newsletter_subscribed', 'gender', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    ordering = ['-created_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    ordering = ['-created_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    ordering = ['-created_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email']
    inlines = [OrderItemInline]
    ordering = ['-created_at']
    readonly_fields = ['order_number', 'created_at', 'updated_at']

    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        action = 'Updated' if change else 'Created'
        logger.info(
            'Order %s by %s (ID=%s) %s by admin user %s',
            obj.order_number,
            obj.user,
            obj.pk,
            action,
            request.user.username,
        )

    def delete_model(self, request, obj):
        order_number = obj.order_number
        user = obj.user
        pk = obj.pk
        super().delete_model(request, obj)
        logger.info(
            'Order %s by %s (ID=%s) deleted by admin user %s',
            order_number,
            user,
            pk,
            request.user.username,
        )

    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f"{updated} orders marked as processing.")

    mark_as_processing.short_description = "Mark selected orders as processing"

    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f"{updated} orders marked as shipped.")

    mark_as_shipped.short_description = "Mark selected orders as shipped"

    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f"{updated} orders marked as delivered.")

    mark_as_delivered.short_description = "Mark selected orders as delivered"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} orders marked as cancelled.")

    mark_as_cancelled.short_description = "Mark selected orders as cancelled"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'total_price']
    list_filter = ['order__status']
    search_fields = ['order__order_number', 'product__name']
    ordering = ['-order__created_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'title', 'helpful_count', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'product__name', 'title']
    ordering = ['-created_at']


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'active', 'order', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['order', '-created_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'order', 'payment_method', 'status', 'amount', 'currency', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['payment_id', 'order__order_number', 'order__user__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'response_data']

    actions = ['mark_payment_completed']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        action = 'Updated' if change else 'Created'
        logger.info(
            'Payment %s for order %s (ID=%s) %s by admin user %s',
            obj.payment_id,
            obj.order.order_number,
            obj.pk,
            action,
            request.user.username,
        )

    def delete_model(self, request, obj):
        payment_id = obj.payment_id
        order_number = obj.order.order_number
        pk = obj.pk
        super().delete_model(request, obj)
        logger.info(
            'Payment %s for order %s (ID=%s) deleted by admin user %s',
            payment_id,
            order_number,
            pk,
            request.user.username,
        )

    def mark_payment_completed(self, request, queryset):
        updated = 0
        for payment in queryset:
            payment.mark_as_completed()
            updated += 1
        self.message_user(request, f"{updated} payments marked as completed.")

    mark_payment_completed.short_description = "Mark selected payments as completed"


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['refund_id', 'payment', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['refund_id', 'payment__payment_id', 'payment__order__order_number']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'response_data']

    actions = ['mark_refund_completed']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        action = 'Updated' if change else 'Created'
        logger.info(
            'Refund %s for payment %s (ID=%s) %s by admin user %s',
            obj.refund_id,
            obj.payment.payment_id,
            obj.pk,
            action,
            request.user.username,
        )

    def delete_model(self, request, obj):
        refund_id = obj.refund_id
        payment_id = obj.payment.payment_id
        pk = obj.pk
        super().delete_model(request, obj)
        logger.info(
            'Refund %s for payment %s (ID=%s) deleted by admin user %s',
            refund_id,
            payment_id,
            pk,
            request.user.username,
        )

    def mark_refund_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} refunds marked as completed.")

    mark_refund_completed.short_description = "Mark selected refunds as completed"

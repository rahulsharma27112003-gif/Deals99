from django.contrib import admin
from django.db import models
from django.utils.safestring import mark_safe
import logging
import csv
from django.http import HttpResponse

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
from core.admin import AdminBaseMixin, RoleBasedAdminMixin


logger = logging.getLogger('api')


def export_as_csv_action(description="Export selected rows as CSV"):
    def export_as_csv(modeladmin, request, queryset):
        meta = modeladmin.model._meta
        field_names = [f.name for f in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            row = [getattr(obj, field) for field in field_names]
            writer.writerow(row)
        return response

    export_as_csv.short_description = description
    return export_as_csv


@admin.register(Category)
class CategoryAdmin(AdminBaseMixin, admin.ModelAdmin):
    list_display = ['name', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_per_page = 25
    save_as = True
    save_on_top = True
    actions = [export_as_csv_action()]


@admin.register(Subcategory)
class SubcategoryAdmin(AdminBaseMixin, admin.ModelAdmin):
    list_display = ['name', 'parent_category', 'active', 'created_at']
    list_filter = ['parent_category', 'active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['parent_category', 'name']
    autocomplete_fields = ('parent_category',)
    save_as = True
    save_on_top = True
    actions = [export_as_csv_action()]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


def export_as_csv_action(description="Export selected rows as CSV"):
    def export_as_csv(modeladmin, request, queryset):
        meta = modeladmin.model._meta
        field_names = [f.name for f in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            row = [getattr(obj, field) for field in field_names]
            writer.writerow(row)
        return response

    export_as_csv.short_description = description
    return export_as_csv


@admin.register(Product)
class ProductAdmin(AdminBaseMixin, admin.ModelAdmin):
    list_display = ['primary_image_thumbnail', 'name', 'category', 'price', 'stock', 'active', 'featured', 'created_at']
    list_display_links = ('name',)
    list_editable = ('price', 'stock', 'active', 'featured')
    list_filter = ['category', 'active', 'featured', 'created_at']
    search_fields = ['name', 'description']
    inlines = [ProductImageInline]
    ordering = ['-created_at']
    list_select_related = ('category',)
    autocomplete_fields = ('category', 'subcategory')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'subcategory', 'active', 'featured')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'mrp', 'stock')
        }),
    )
    actions = [export_as_csv_action(), 'mark_as_active', 'mark_as_inactive', 'restock_selected']

    def primary_image_thumbnail(self, obj):
        img = obj.images.filter(is_primary=True).first()
        if img and hasattr(img, 'image') and getattr(img.image, 'url', None):
            return mark_safe(f"<img src='{img.image.url}' style='height:40px;'/>")
        return "-"

    primary_image_thumbnail.short_description = 'Image'

    def mark_as_active(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f"{updated} products marked active.")

    mark_as_active.short_description = "Mark selected products as active"

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f"{updated} products marked inactive.")

    mark_as_inactive.short_description = "Mark selected products as inactive"

    def restock_selected(self, request, queryset):
        updated = queryset.update(stock=models.F('stock') + 10)
        self.message_user(request, f"{updated} products restocked by 10 units.")

    restock_selected.short_description = "Restock selected products by 10"


@admin.register(ProductImage)
class ProductImageAdmin(AdminBaseMixin, admin.ModelAdmin):
    list_display = ['product', 'is_primary', 'image_preview', 'created_at']
    list_filter = ['is_primary', 'created_at']
    ordering = ['-created_at']
    readonly_fields = ('image_preview',)
    autocomplete_fields = ('product',)
    list_select_related = ('product',)
    actions = [export_as_csv_action()]

    def image_preview(self, obj):
        if obj.image and getattr(obj.image, 'url', None):
            return mark_safe(f"<img src='{obj.image.url}' style='height:60px;' />")
        return '-'

    image_preview.short_description = 'Preview'


@admin.register(UserProfile)
class UserProfileAdmin(AdminBaseMixin, admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'newsletter_subscribed', 'created_at']
    list_filter = ['role', 'newsletter_subscribed', 'gender', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    ordering = ['-created_at']
    autocomplete_fields = ('user',)
    list_select_related = ('user',)
    actions = [export_as_csv_action()]


@admin.register(Cart)
class CartAdmin(AdminBaseMixin, admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    ordering = ['-created_at']
    autocomplete_fields = ('user', 'product')
    list_select_related = ('user', 'product')
    actions = [export_as_csv_action()]


@admin.register(Wishlist)
class WishlistAdmin(AdminBaseMixin, admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    ordering = ['-created_at']
    autocomplete_fields = ('user', 'product')
    list_select_related = ('user', 'product')
    actions = [export_as_csv_action()]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(RoleBasedAdminMixin, AdminBaseMixin, admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email']
    inlines = [OrderItemInline]
    ordering = ['-created_at']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    autocomplete_fields = ('user',)
    list_select_related = ('user',)
    date_hierarchy = 'created_at'

    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled', export_as_csv_action()]

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
class OrderItemAdmin(AdminBaseMixin, admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'total_price']
    list_filter = ['order__status']
    search_fields = ['order__order_number', 'product__name']
    ordering = ['-order__created_at']
    autocomplete_fields = ('order', 'product')
    list_select_related = ('order', 'product')
    actions = [export_as_csv_action()]


@admin.register(Review)
class ReviewAdmin(AdminBaseMixin, admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'title', 'helpful_count', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'product__name', 'title']
    ordering = ['-created_at']
    autocomplete_fields = ('user', 'product')
    list_select_related = ('user', 'product')
    actions = [export_as_csv_action()]


@admin.register(Banner)
class BannerAdmin(RoleBasedAdminMixin, admin.ModelAdmin):
    allowed_roles = ['ADMIN', 'MANAGER']
    list_display = ['title', 'active', 'order', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['order', '-created_at']
    actions = [export_as_csv_action()]


@admin.register(Payment)
class PaymentAdmin(RoleBasedAdminMixin, AdminBaseMixin, admin.ModelAdmin):
    allowed_roles = ['ADMIN', 'MANAGER']
    list_display = ['payment_id', 'order', 'payment_method', 'status', 'amount', 'currency', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['payment_id', 'order__order_number', 'order__user__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'response_data']
    autocomplete_fields = ('order',)
    list_select_related = ('order',)
    date_hierarchy = 'created_at'

    actions = ['mark_payment_completed', export_as_csv_action()]

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
class RefundAdmin(RoleBasedAdminMixin, AdminBaseMixin, admin.ModelAdmin):
    allowed_roles = ['ADMIN', 'MANAGER']
    list_display = ['refund_id', 'payment', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['refund_id', 'payment__payment_id', 'payment__order__order_number']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'response_data']
    autocomplete_fields = ('payment',)
    list_select_related = ('payment',)
    date_hierarchy = 'created_at'

    actions = ['mark_refund_completed', export_as_csv_action()]

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

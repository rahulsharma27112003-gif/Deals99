from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'content_type', 'object_repr', 'actor', 'timestamp')
    list_filter = ('action', 'content_type', 'actor', 'timestamp')
    search_fields = ('object_repr', 'actor__email', 'actor__username')
    readonly_fields = ('action', 'content_type', 'object_id', 'object_repr', 'changes', 'actor', 'ip_address', 'timestamp', 'extra')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class AdminBaseMixin:
    """Shared admin settings for easier add/edit workflows."""
    save_on_top = True
    save_as = True
    actions_on_top = True
    actions_on_bottom = True
    show_full_result_count = True
    list_per_page = 40
    empty_value_display = '—'
    save_as_continue = False

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


class RoleBasedAdminMixin:
    """Mixin to restrict admin access based on `User.role`.

    Usage: add `allowed_roles = ['ADMIN','MANAGER']` on ModelAdmin classes.
    Superusers bypass checks.
    """
    allowed_roles = None

    def _role_allowed(self, request):
        if request.user and request.user.is_superuser:
            return True
        if not request.user or not getattr(request.user, 'is_authenticated', False):
            return False
        if not self.allowed_roles:
            return True
        user_role = getattr(request.user, 'role', None) or getattr(getattr(request.user, 'profile', None), 'role', None)
        return user_role in self.allowed_roles

    def has_module_permission(self, request):
        return self._role_allowed(request)

    def has_view_permission(self, request, obj=None):
        return self._role_allowed(request)

    def has_change_permission(self, request, obj=None):
        return self._role_allowed(request)

    def has_add_permission(self, request):
        return self._role_allowed(request)

    def has_delete_permission(self, request, obj=None):
        return self._role_allowed(request)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active', 'is_email_verified')
    list_filter = ('role', 'is_staff', 'is_active', 'is_email_verified')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'groups', 'user_permissions')}),
        (_('Security & status'), {'fields': ('failed_login_attempts', 'locked_until')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

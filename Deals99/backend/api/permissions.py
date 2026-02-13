from rest_framework.permissions import BasePermission


def _get_user_role(user) -> str:
    """Resolve role from the new custom User model when available.

    Priority:
    1. user.role (custom User)
    2. user.profile.role (legacy UserProfile)
    3. Django flags (is_superuser / is_staff)
    4. anonymous/customer fallback
    """
    if not user or not user.is_authenticated:
        return 'anonymous'

    # Prefer explicit role on the user if available
    role = getattr(user, 'role', None)
    if role:
        return role.lower() if isinstance(role, str) else role

    # Backward-compatibility: check legacy profile.role if present
    profile = getattr(user, 'profile', None)
    role = getattr(profile, 'role', None)
    if role:
        return role

    # Superuser and staff fallbacks
    if user.is_superuser:
        return 'super_admin'
    if user.is_staff:
        return 'staff'

    return 'customer'


class IsAdminOrManager(BasePermission):
    """
    Allows access only to users with at least Manager-level permissions.

    Role hierarchy:
        Super Admin > Admin > Manager > Staff > Customer
    """

    allowed_roles = {'super_admin', 'admin', 'manager'}

    def has_permission(self, request, view) -> bool:
        role = _get_user_role(request.user)
        # Also allow any Django staff member for backward compatibility
        return role in self.allowed_roles or bool(request.user and request.user.is_staff)


class IsStaffOrAbove(BasePermission):
    """
    Allows access to internal staff:
        Super Admin, Admin, Manager, Staff
    """

    allowed_roles = {'super_admin', 'admin', 'manager', 'staff'}

    def has_permission(self, request, view) -> bool:
        role = _get_user_role(request.user)
        return role in self.allowed_roles


class IsSuperAdmin(BasePermission):
    """Restrict access to super administrators only."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


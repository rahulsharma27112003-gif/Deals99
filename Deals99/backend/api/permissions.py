from rest_framework.permissions import BasePermission

# Map custom User.role values (e.g. SUPERADMIN) to permission slugs
_ROLE_ALIASES = {
    'superadmin': 'super_admin',
    'super_admin': 'super_admin',
    'admin': 'admin',
    'manager': 'manager',
    'staff': 'staff',
    'customer': 'customer',
}


def _normalize_role(role: str) -> str:
    if not role:
        return 'customer'
    key = role.lower() if isinstance(role, str) else str(role).lower()
    return _ROLE_ALIASES.get(key, key)


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
        return _normalize_role(role)

    profile = getattr(user, 'profile', None)
    profile_role = getattr(profile, 'role', None)
    if profile_role:
        return _normalize_role(profile_role)

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

    allowed_roles = {'super_admin', 'admin', 'manager', 'staff', 'superadmin'}

    def has_permission(self, request, view) -> bool:
        role = _get_user_role(request.user)
        return role in self.allowed_roles or bool(request.user and request.user.is_staff)


class IsSuperAdmin(BasePermission):
    """Restrict access to super administrators only."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


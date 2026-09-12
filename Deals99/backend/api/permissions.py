from rest_framework.permissions import BasePermission

# Canonical role values must be a single, backend-authoritative representation.
_ROLE_ALIASES = {
    'SUPERADMIN': 'SUPERADMIN',
    'SUPER_ADMIN': 'SUPERADMIN',
    'SUPERADMINISTRATOR': 'SUPERADMIN',
    'ADMIN': 'ADMIN',
    'MANAGER': 'MANAGER',
    'STAFF': 'STAFF',
    'CUSTOMER': 'CUSTOMER',
    'ANONYMOUS': 'ANONYMOUS',
}


def _normalize_role(role: str) -> str:
    if not role:
        return 'CUSTOMER'
    normalized = str(role).strip()
    if not normalized:
        return 'CUSTOMER'

    value = normalized.replace('-', '_').replace(' ', '_').upper()
    return _ROLE_ALIASES.get(value, value)


def _get_user_role(user) -> str:
    """Resolve role from the new custom User model when available.

    Priority:
    1. user.role (custom User)
    2. user.profile.role (legacy UserProfile)
    3. Django flags (is_superuser / is_staff)
    4. anonymous/customer fallback
    """
    if not user or not user.is_authenticated:
        return 'ANONYMOUS'

    # Prefer explicit role on the user if available
    role = getattr(user, 'role', None)
    if role:
        return _normalize_role(role)

    profile = getattr(user, 'profile', None)
    profile_role = getattr(profile, 'role', None)
    if profile_role:
        return _normalize_role(profile_role)

    if user.is_superuser:
        return 'SUPERADMIN'
    if user.is_staff:
        return 'STAFF'

    return 'CUSTOMER'


class IsAdminOrManager(BasePermission):
    """
    Allows access only to users with at least Manager-level permissions.

    Role hierarchy:
        SUPERADMIN > ADMIN > MANAGER > STAFF > CUSTOMER
    """

    allowed_roles = {'SUPERADMIN', 'ADMIN', 'MANAGER'}

    def has_permission(self, request, view) -> bool:
        role = _get_user_role(request.user)
        return role in self.allowed_roles or bool(request.user and request.user.is_staff)


class IsStaffOrAbove(BasePermission):
    """
    Allows access to internal staff:
        SUPERADMIN, ADMIN, MANAGER, STAFF
    """

    allowed_roles = {'SUPERADMIN', 'ADMIN', 'MANAGER', 'STAFF'}

    def has_permission(self, request, view) -> bool:
        role = _get_user_role(request.user)
        return role in self.allowed_roles or bool(request.user and request.user.is_staff)


class IsSuperAdmin(BasePermission):
    """Restrict access to super administrators only."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and _get_user_role(request.user) == 'SUPERADMIN')


"""
TradeMind AI - DRF Permission Classes
=======================================
Centralised permission layer for all API views.

Usage
-----
    from core.permissions import IsPremiumUser, RBACPermission

    class MyView(APIView):
        permission_classes = [IsAuthenticated, IsPremiumUser]

    class AnotherView(APIView):
        permission_classes = [IsAuthenticated, RBACPermission]
        required_permissions = ["orders.create", "orders.view"]
"""

import logging
from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

logger = logging.getLogger("trademind.permissions")


# ---------------------------------------------------------------------------
# Role constants (mirror the choices in apps.accounts.models)
# ---------------------------------------------------------------------------
ROLE_FREE = "free"
ROLE_PREMIUM = "premium"
ROLE_ENTERPRISE = "enterprise"
ROLE_ADMIN = "admin"
ROLE_SUPER_ADMIN = "super_admin"

# Ordered hierarchy (higher index = more privileges)
ROLE_HIERARCHY = [
    ROLE_FREE,
    ROLE_PREMIUM,
    ROLE_ENTERPRISE,
    ROLE_ADMIN,
    ROLE_SUPER_ADMIN,
]


def _has_role_or_above(user: Any, min_role: str) -> bool:
    """
    Return True if the user's role is `min_role` or higher in the hierarchy.
    Raises no exceptions — returns False for any unexpected state.
    """
    try:
        user_role = getattr(user, "role", ROLE_FREE)
        return ROLE_HIERARCHY.index(user_role) >= ROLE_HIERARCHY.index(min_role)
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# Base permission with audit logging
# ---------------------------------------------------------------------------

class _AuditedPermission(permissions.BasePermission):
    """Internal base that logs every permission denial for audit trails."""

    def _deny(self, request: Request, reason: str) -> bool:
        logger.warning(
            "Permission denied",
            extra={
                "user_id": str(getattr(request.user, "id", "anonymous")),
                "permission_class": self.__class__.__name__,
                "method": request.method,
                "path": request.path,
                "reason": reason,
            },
        )
        return False


# ---------------------------------------------------------------------------
# 1. IsAdminUser
# ---------------------------------------------------------------------------

class IsAdminUser(_AuditedPermission):
    """
    Allow access only to users with `role == 'admin'` or `role == 'super_admin'`.
    Also respects Django's is_staff flag for backwards compatibility.
    """

    message = "You must be an administrator to perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return self._deny(request, "unauthenticated")

        if request.user.is_staff or _has_role_or_above(request.user, ROLE_ADMIN):
            return True

        return self._deny(request, f"role={getattr(request.user, 'role', 'unknown')}")


# ---------------------------------------------------------------------------
# 2. IsSuperAdmin
# ---------------------------------------------------------------------------

class IsSuperAdmin(_AuditedPermission):
    """
    Allow access only to users with `role == 'super_admin'`.
    Also respects Django's is_superuser flag.
    """

    message = "You must be a super-administrator to perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return self._deny(request, "unauthenticated")

        if request.user.is_superuser or _has_role_or_above(request.user, ROLE_SUPER_ADMIN):
            return True

        return self._deny(request, f"role={getattr(request.user, 'role', 'unknown')}")


# ---------------------------------------------------------------------------
# 3. IsPremiumUser
# ---------------------------------------------------------------------------

class IsPremiumUser(_AuditedPermission):
    """
    Allow access to users on Premium, Enterprise, Admin, or Super-Admin plans.
    Free-tier users are rejected.
    """

    message = "This feature requires a Premium subscription."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return self._deny(request, "unauthenticated")

        if _has_role_or_above(request.user, ROLE_PREMIUM):
            return True

        return self._deny(request, "free-tier user")


# ---------------------------------------------------------------------------
# 4. IsEnterpriseUser
# ---------------------------------------------------------------------------

class IsEnterpriseUser(_AuditedPermission):
    """
    Allow access to users on Enterprise, Admin, or Super-Admin plans.
    """

    message = "This feature requires an Enterprise subscription."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return self._deny(request, "unauthenticated")

        if _has_role_or_above(request.user, ROLE_ENTERPRISE):
            return True

        return self._deny(request, f"role={getattr(request.user, 'role', 'unknown')}")


# ---------------------------------------------------------------------------
# 5. IsTenantMember
# ---------------------------------------------------------------------------

class IsTenantMember(_AuditedPermission):
    """
    Object-level permission: verify the requesting user belongs to the same
    tenant as the object being accessed.

    Expects:
        - request.user.tenant_id  : UUID of the authenticated user's tenant
        - obj.tenant_id           : UUID stored on the model instance

    Safe HTTP methods (GET, HEAD, OPTIONS) are additionally gated so that
    cross-tenant data leaks are impossible even for read-only access.
    """

    message = "You do not have access to resources belonging to this tenant."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """View-level check: user must be authenticated and have a tenant_id."""
        if not request.user or not request.user.is_authenticated:
            return self._deny(request, "unauthenticated")

        if not getattr(request.user, "tenant_id", None):
            return self._deny(request, "no tenant_id on user")

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        """Object-level check: tenant_ids must match."""
        # Super-admins bypass tenant isolation (platform-level access)
        if getattr(request.user, "is_superuser", False) or _has_role_or_above(
            request.user, ROLE_SUPER_ADMIN
        ):
            return True

        user_tenant = getattr(request.user, "tenant_id", None)
        obj_tenant = getattr(obj, "tenant_id", None)

        if user_tenant and obj_tenant and str(user_tenant) == str(obj_tenant):
            return True

        return self._deny(
            request,
            f"user_tenant={user_tenant} != obj_tenant={obj_tenant}",
        )


# ---------------------------------------------------------------------------
# 6. RBACPermission
# ---------------------------------------------------------------------------

class RBACPermission(_AuditedPermission):
    """
    Role-Based Access Control permission.

    Views declare the required permissions as a class attribute or override
    `get_required_permissions()`:

        class OrderCreateView(APIView):
            permission_classes = [IsAuthenticated, RBACPermission]
            required_permissions = ["orders.create"]

    The user model must expose a `has_permission(perm: str) -> bool` method
    OR a `permissions` iterable of permission strings.

    Super-admins and platform admins always pass.
    """

    message = "You do not have the required permissions to perform this action."

    def get_required_permissions(self, request: Request, view: APIView) -> list[str]:
        """
        Return the list of permission strings required by the view.
        Checks `required_permissions` class attribute first, then falls back
        to an empty list (no specific permission required).
        """
        return list(getattr(view, "required_permissions", []))

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return self._deny(request, "unauthenticated")

        # Platform admins bypass RBAC
        if request.user.is_superuser or _has_role_or_above(request.user, ROLE_ADMIN):
            return True

        required = self.get_required_permissions(request, view)

        if not required:
            return True  # No specific permissions required

        for perm in required:
            if not self._user_has_perm(request.user, perm):
                return self._deny(request, f"missing permission: {perm}")

        return True

    @staticmethod
    def _user_has_perm(user: Any, perm: str) -> bool:
        """
        Evaluate whether `user` holds `perm`.

        Tries several strategies in order:
        1. Custom `has_perm(perm)` method on the user model
        2. `user.permissions` iterable
        3. Django's built-in `user.has_perm(perm)`
        """
        # Strategy 1 — custom method
        custom_checker = getattr(user, "has_perm", None)
        if callable(custom_checker):
            try:
                return bool(custom_checker(perm))
            except Exception:
                pass

        # Strategy 2 — permissions iterable
        user_perms = getattr(user, "permissions", None)
        if user_perms is not None:
            try:
                return perm in user_perms
            except TypeError:
                pass

        return False

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        """
        Object-level RBAC: same check as has_permission.
        Views can override this by supplying `object_required_permissions`.
        """
        if not request.user or not request.user.is_authenticated:
            return self._deny(request, "unauthenticated")

        if request.user.is_superuser or _has_role_or_above(request.user, ROLE_ADMIN):
            return True

        required = list(getattr(view, "object_required_permissions", []))
        if not required:
            return True

        for perm in required:
            if not self._user_has_perm(request.user, perm):
                return self._deny(request, f"missing object permission: {perm}")

        return True


# ---------------------------------------------------------------------------
# Composite helpers
# ---------------------------------------------------------------------------

class IsAuthenticatedAndActive(_AuditedPermission):
    """
    Ensure the user is authenticated AND their account is not suspended/deactivated.
    Use this instead of the plain `IsAuthenticated` for endpoints that
    should not be accessible to suspended users.
    """

    message = "Your account is not active. Please contact support."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return self._deny(request, "unauthenticated")

        if not request.user.is_active:
            return self._deny(request, "account inactive")

        return True


class IsOwnerOrAdmin(_AuditedPermission):
    """
    Object-level permission: allow access if the requesting user is the owner
    of the object (obj.user_id == request.user.id) OR is an admin/super-admin.

    Expects objects to have either `user_id` or `user` (FK) attribute.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if not request.user or not request.user.is_authenticated:
            return self._deny(request, "unauthenticated")

        if request.user.is_superuser or _has_role_or_above(request.user, ROLE_ADMIN):
            return True

        # Try obj.user_id first, then obj.user.id
        obj_user_id = getattr(obj, "user_id", None)
        if obj_user_id is None:
            user_rel = getattr(obj, "user", None)
            obj_user_id = getattr(user_rel, "id", None)

        if obj_user_id and str(obj_user_id) == str(request.user.id):
            return True

        return self._deny(
            request,
            f"user {request.user.id} is not owner of obj {getattr(obj, 'pk', '?')}",
        )

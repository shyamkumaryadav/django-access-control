from django.db.models import Subquery
from rest_framework.permissions import BasePermission

from .exceptions import Unauthorized
from .models import Org, UserOrgRole
from .utils import ROLE_ADMIN, ROLE_PI, ROLE_READ_ONLY, ROLE_SI, ROLE_SUPERUSER

ROLE_PERMISSIONS = {
    ROLE_SUPERUSER: ["*"],
    ROLE_ADMIN: [
        "org.view",
        "org.edit",
        "org.list",
        "project.view",
        "project.edit",
        "project.list",
        "project.create",
    ],
    ROLE_PI: [
        "org.view",
        "org.list",
        "project.view",
        "project.edit",
        "project.list",
        "project.create",
        "project.delete",
    ],
    ROLE_READ_ONLY: [
        "org.list",
        "project.list",
    ],
    ROLE_SI: [
        "org.view",
        "project.view",
        "project.list",
    ],
}

DEFAULT_ACTION_MAP = {
    "list": "list",
    "retrieve": "view",
    "create": "create",
    "update": "edit",
    "partial_update": "edit",
    "destroy": "delete",
}


class RolePermission(BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):

        if self.check_user(request):
            return True

        resource, action, permission_code = self.get_permission_code(view)

        if not permission_code:
            return False

        # /orgs/
        # Let queryset decide visible orgs. If none, return [].
        if resource == "org" and action == "list":
            return True

        # /orgs/<org_id>/projects/
        # For nested project list/create, org_id is available in URL.
        org_id = self.get_org_id_from_view(view)

        if org_id:
            role = self.get_cached_user_role_for_org_id(
                request=request,
                org_id=org_id,
            )
            return self.role_has_permission(
                role=role,
                permission_code=permission_code,
            )

        # Detail actions:
        # /orgs/<id>/
        # /orgs/<org_id>/projects/<id>/
        # Object-level permission will check actual org access.
        if action in ["view", "edit", "delete"]:
            return True

        # Example: /orgs/ create
        # Normal users have no org context here.
        # Superuser already returned True above.
        return False

    def has_object_permission(self, request, view, obj):
        if self.check_user(request):
            return True

        _, _, permission_code = self.get_permission_code(view)

        if not permission_code:
            return False

        org_id = self.get_org_id_from_object(obj)

        if not org_id:
            return False

        # Reuse annotated role from the object
        if hasattr(obj, "current_user_role"):
            role = obj.current_user_role
        # Reuse annotated role from a cached related Org
        elif "org" in obj._state.fields_cache and hasattr(
            obj.org,
            "current_user_role",
        ):
            role = obj.org.current_user_role
        # Fall back to existing request-cached SQL lookup
        else:
            role = self.get_cached_user_role_for_org_id(
                request=request,
                org_id=org_id,
            )

        return self.role_has_permission(
            role=role,
            permission_code=permission_code,
        )

    def check_user(self, request):
        if not request.user.is_authenticated:
            # DRF converts NotAuthenticated (401) to 403 when using
            # SessionAuthentication because it does not provide a
            # WWW-Authenticate header. use custom Unauthorized to force
            # 401 for unauthenticated requests.
            raise Unauthorized()
        return request.user.is_superuser

    def get_permission_code(self, view):
        resource = self.get_resource_name(view)
        action = self.get_business_action(view)
        return (
            resource,
            action,
            f"{resource}.{action}" if resource and action else None,
        )

    def get_resource_name(self, view):
        """
        Get resource name automatically.

        OrgViewSet queryset model      -> org
        ProjectViewSet queryset model  -> project

        Optional override:
            permission_resource = "project"
        """
        if hasattr(view, "permission_resource"):
            return view.permission_resource
        queryset = getattr(view, "queryset", None)
        if queryset is None and hasattr(view, "get_queryset"):
            try:
                queryset = view.get_queryset()
            except Exception:
                queryset = None
        if queryset is not None:
            return queryset.model._meta.model_name
        return None

    def get_business_action(self, view):
        action = getattr(view, "action", None)
        action_map = {
            **DEFAULT_ACTION_MAP,
            **getattr(view, "permission_action_map", {}),
        }
        return action_map.get(action)

    def get_org_id_from_view(self, view):
        """
        Resolve org id from nested URL.

        Example:
            /orgs/<org_id>/projects/
        """
        return view.kwargs.get("org_id")

    def get_org_id_from_object(self, obj):
        """
        Resolve org id from object without fetching full org.

        Org object:
            obj.id

        Project object:
            obj.org_id
        """
        model_name = obj.__class__._meta.model_name
        if model_name == "org":
            return obj.id
        if hasattr(obj, "org_id"):
            return obj.org_id
        return None

    def get_cached_user_role_for_org_id(self, request, org_id):
        """
        Cache org role on the underlying Django HttpRequest.

        Why:
        - DRF Request is a wrapper.
        - Browsable API may create/use repeated permission checks.
        - request._request is the real Django request for the current HTTP.
        """
        user = request.user
        cache_key = f"org_role:{user.id}:{org_id}"
        django_request = request._request
        if not hasattr(django_request, "_rbac_role_cache"):
            django_request._rbac_role_cache = {}
        if cache_key not in django_request._rbac_role_cache:
            user_role = self.get_user_role_for_org_id(
                user=user,
                org_id=org_id,
            )
            django_request._rbac_role_cache[cache_key] = user_role
        return django_request._rbac_role_cache[cache_key]

    def get_user_role_for_org_id(self, user, org_id):
        """
        Resolve user's effective role for one org.

        Uses one DB query for non-superuser:
        - Checks Org.admin_id.
        - Checks UserOrgRole.role using Subquery.
        """
        if not org_id:
            return None
        org_role = (
            Org.objects.filter(id=org_id)
            .annotate(
                matched_role=Subquery(
                    UserOrgRole.objects.filter(
                        user=user,
                        org_id=org_id,
                    ).values(
                        "role"
                    )[:1]
                )
            )
            .values("admin_id", "matched_role")
            .first()
        )
        if not org_role:
            return None
        if org_role["admin_id"] == user.id:
            return ROLE_ADMIN
        return org_role["matched_role"]

    def role_has_permission(self, role, permission_code):
        if not role:
            return False
        permissions = ROLE_PERMISSIONS.get(role, [])
        if "*" in permissions:
            return True
        return permission_code in permissions

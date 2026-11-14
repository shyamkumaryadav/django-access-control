"""

Serializers for RBAC API.

Reference: LR3 - Permission Routing & Querysets

"""

from typing import Any, cast

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Org, Project, UserOrgRole
from .permissions import ROLE_ADMIN, ROLE_PERMISSIONS, ROLE_SUPERUSER


class MultiLookupHyperlinkedIdentityField(
    serializers.HyperlinkedIdentityField,
):

    lookup_fields: dict[str, str]

    def __init__(
        self,
        *args: Any,
        lookup_fields: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:

        self.lookup_fields = lookup_fields or {"pk": "pk"}

        super().__init__(*args, **kwargs)

    def get_url(
        self,
        obj: Any,
        view_name: str,
        request: Any,
        format: str | None,
    ) -> str | None:
        """Build URL using multiple lookup fields."""

        if obj.pk is None:

            return None

        url_kwargs: dict[str, Any] = {}

        for url_kwarg, model_field in self.lookup_fields.items():

            value = getattr(obj, model_field, None)

            if value is None:

                return None

            url_kwargs[url_kwarg] = value

        return cast(
            "str | None",
            self.reverse(
                view_name,
                kwargs=url_kwargs,
                request=request,
                format=format,
            ),
        )


class UserSerializer(serializers.ModelSerializer):

    class Meta:

        model = User

        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
        ]

        read_only_fields = ["id"]


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_staff",
            "is_superuser",
        ]


class FakeLoginSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        label="Select User",
    )


class UserOrgRoleSerializer(serializers.ModelSerializer):

    user_username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    url = serializers.HyperlinkedIdentityField(
        view_name="userorgrole-detail",
        lookup_field="id",
    )

    class Meta:

        model = UserOrgRole

        fields = [
            "id",
            "url",
            "user",
            "user_username",
            "org",
            "role",
            "created_at",
        ]

        read_only_fields = ["id", "url", "created_at"]


class OrgSerializer(serializers.ModelSerializer):

    admin_username = serializers.CharField(
        source="admin.username",
        read_only=True,
    )

    user_role = serializers.SerializerMethodField()

    user_permissions = serializers.SerializerMethodField()

    url = serializers.HyperlinkedIdentityField(
        view_name="org-detail",
        lookup_field="pk",
    )

    project_url = MultiLookupHyperlinkedIdentityField(
        view_name="org-projects-list", lookup_fields={"org_id": "pk"}
    )

    class Meta:

        model = Org

        fields = [
            "id",
            "url",
            "project_url",
            "name",
            "slug",
            "admin",
            "admin_username",
            "user_role",
            "user_permissions",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "url",
            "admin_username",
            "user_role",
            "user_permissions",
            "created_at",
        ]

    def get_user_role(self, obj):

        user = self.context["request"].user

        if user.is_superuser:

            return ROLE_SUPERUSER

        if obj.admin_id == user.id:

            return ROLE_ADMIN

        return (
            UserOrgRole.objects.filter(
                user=user,
                org=obj,
            )
            .values_list(
                "role",
                flat=True,
            )
            .first()
        )

    def get_user_permissions(self, obj):

        role = self.get_user_role(obj)

        if not role:

            return []

        return ROLE_PERMISSIONS.get(role, [])


class ProjectSerializer(serializers.ModelSerializer):

    org_name = serializers.CharField(source="org.name", read_only=True)

    url = MultiLookupHyperlinkedIdentityField(
        view_name="org-projects-detail",
        lookup_fields={
            "org_id": "org_id",
            "pk": "pk",
        },
    )

    class Meta:

        model = Project

        fields = [
            "id",
            "url",
            "name",
            "org",
            "org_name",
            "description",
            "created_at",
            "updated_at",
        ]

        read_only_fields = ["id", "url", "created_at", "org", "updated_at"]

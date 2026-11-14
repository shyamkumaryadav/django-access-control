"""
Serializers for RBAC API.
Reference: LR3 - Permission Routing & Querysets
"""
from typing import Any, cast
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Org, UserOrgRole, Project
from .permissions import (
    ROLE_ADMIN,
    ROLE_PERMISSIONS,
    ROLE_SUPERUSER,
)


class MultiLookupHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    """
    Custom hyperlink field that supports multiple lookup fields.
    Allows building URLs with composite parameters like:
    /api/orgs/{org_id}/projects/{project_id}/
    
    Usage:
        url = MultiLookupHyperlinkedIdentityField(
            view_name='org-projects-detail',
            lookup_fields={'org_id': 'org_id', 'pk': 'pk'}
        )
    """
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
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class FakeLoginSerializer(serializers.Serializer):
    """
    Serializer for fake login form - select user from dropdown.
    Renders as interactive form in browsable API with user choices.
    """
    user_id = serializers.ChoiceField(
        choices=[],  # Will be populated dynamically
        label="Select User to Login As",
        help_text="Choose a user from the dropdown to switch to that user"
    )
    
    def __init__(self, *args, **kwargs):
        """Dynamically populate user choices."""
        super().__init__(*args, **kwargs)
        # Build choices as (id, display_name) tuples
        users = User.objects.all().order_by('is_superuser', 'username')
        choices = []
        for user in users:
            display_name = f"{user.username} ({user.email})"
            if user.is_superuser:
                display_name += " [SUPERUSER]"
            choices.append((user.id, display_name))
        self.fields['user_id'].choices = choices
    
    def validate_user_id(self, value):
        """Validate that user exists and return the user ID as integer."""
        try:
            int_value = int(value)
            User.objects.get(id=int_value)
            return int_value
        except (User.DoesNotExist, ValueError):
            raise serializers.ValidationError(f"Invalid user selection")


class UserOrgRoleSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='userorgrole-detail',
        lookup_field='id'
    )

    class Meta:
        model = UserOrgRole
        fields = ['id', 'url', 'user', 'user_username', 'org', 'role', 'created_at']
        read_only_fields = ['id', 'url', 'created_at']


class OrgSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    user_role = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(
        view_name='org-detail',
        lookup_field='pk'
    )
    project_url = MultiLookupHyperlinkedIdentityField(
        view_name='org-projects-list',
        lookup_fields={'org_id': 'pk'}
    )

    class Meta:
        model = Org
        fields = ['id', 'url', 'project_url', 'name', 'slug', 'admin', 'admin_username', 'user_role', 'user_permissions', 'created_at',]
        read_only_fields = ['id', 'url', 'admin_username', 'user_role', 'user_permissions', 'created_at']

    def get_user_role(self, obj):
        user = self.context["request"].user

        if user.is_superuser:
            return ROLE_SUPERUSER

        if obj.admin_id == user.id:
            return ROLE_ADMIN

        return (
            UserOrgRole.objects
            .filter(user=user, org=obj)
            .values_list("role", flat=True)
            .first()
        )

    def get_user_permissions(self, obj):
        role = self.get_user_role(obj)

        if not role:
            return []

        return ROLE_PERMISSIONS.get(role, [])


class ProjectSerializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source='org.name', read_only=True)
    url = MultiLookupHyperlinkedIdentityField(
        view_name='org-projects-detail',
        lookup_fields={'org_id': 'org_id', 'pk': 'pk'}
    )

    class Meta:
        model = Project
        fields = ['id', 'url', 'name', 'org', 'org_name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'url', 'created_at', 'org', 'updated_at']

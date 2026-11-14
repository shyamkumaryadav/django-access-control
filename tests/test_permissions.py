"""
Tests for RBAC permission classes.
Reference: LR3 - Permission Routing & Querysets
Reference: LR4 - Role-Based Action Permissions
Reference: Phase 2 in plan.md
"""
import pytest
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User
from core.models import Org, UserOrgRole, Project
from core.permissions import (
    UserBelongsToOrg,
    CanViewProject,
    CanEditProject,
    CanDeleteProject,
)


@pytest.mark.django_db
class TestUserBelongsToOrgPermission:
    """Test UserBelongsToOrg permission class."""

    def test_superuser_always_allowed(self):
        """Superuser is always allowed."""
        factory = APIRequestFactory()
        request = factory.get('/api/orgs/')

        admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
        request.user = admin

        permission = UserBelongsToOrg()
        assert permission.has_permission(request, None) is True

    def test_authenticated_user_with_role(self):
        """Authenticated user with org role is allowed."""
        factory = APIRequestFactory()
        request = factory.get('/api/orgs/')

        admin = User.objects.create_user('admin', 'admin@test.com', 'pass')
        user = User.objects.create_user('user1', 'user1@test.com', 'pass')
        org = Org.objects.create(name='Test', slug='test', admin=admin)
        UserOrgRole.objects.create(user=user, org=org, role='PI')

        request.user = user
        permission = UserBelongsToOrg()
        assert permission.has_permission(request, None) is True

    def test_authenticated_user_without_role(self):
        """Authenticated user without org role is denied."""
        factory = APIRequestFactory()
        request = factory.get('/api/orgs/')

        user = User.objects.create_user('user1', 'user1@test.com', 'pass')
        request.user = user

        permission = UserBelongsToOrg()
        assert permission.has_permission(request, None) is False

    def test_unauthenticated_user_denied(self):
        """Unauthenticated user is denied."""
        factory = APIRequestFactory()
        request = factory.get('/api/orgs/')
        request.user = None

        permission = UserBelongsToOrg()
        assert permission.has_permission(request, None) is False

    def test_object_permission_user_in_org(self):
        """User in org can access org object."""
        factory = APIRequestFactory()
        request = factory.get('/api/orgs/1/')

        admin = User.objects.create_user('admin', 'admin@test.com', 'pass')
        user = User.objects.create_user('user1', 'user1@test.com', 'pass')
        org = Org.objects.create(name='Test', slug='test', admin=admin)
        UserOrgRole.objects.create(user=user, org=org, role='PI')

        request.user = user
        permission = UserBelongsToOrg()
        assert permission.has_object_permission(request, None, org) is True

    def test_object_permission_user_not_in_org(self):
        """User not in org cannot access org object."""
        factory = APIRequestFactory()
        request = factory.get('/api/orgs/1/')

        admin = User.objects.create_user('admin', 'admin@test.com', 'pass')
        user = User.objects.create_user('user1', 'user1@test.com', 'pass')
        org = Org.objects.create(name='Test', slug='test', admin=admin)

        request.user = user
        permission = UserBelongsToOrg()
        assert permission.has_object_permission(request, None, org) is False


@pytest.mark.django_db
class TestCanViewProjectPermission:
    """Test CanViewProject permission class."""

    def test_all_roles_can_view(self, org_admin, pi_user, readonly_user):
        """All roles can view projects in their org."""
        factory = APIRequestFactory()
        request = factory.get('/api/projects/1/')

        _, org = org_admin
        project = Project.objects.create(name='Test', org=org)

        permission = CanViewProject()

        # Test org_admin
        request.user = org_admin[0]
        assert permission.has_object_permission(request, None, project) is True

        # Test PI
        request.user = pi_user[0]
        assert permission.has_object_permission(request, None, project) is True

        # Test read_only
        request.user = readonly_user[0]
        assert permission.has_object_permission(request, None, project) is True

    def test_outsider_cannot_view(self, org_admin, outsider_user):
        """User from outside org cannot view project."""
        factory = APIRequestFactory()
        request = factory.get('/api/projects/1/')

        _, org = org_admin
        project = Project.objects.create(name='Test', org=org)

        request.user = outsider_user
        permission = CanViewProject()
        assert permission.has_object_permission(request, None, project) is False


@pytest.mark.django_db
class TestCanEditProjectPermission:
    """Test CanEditProject permission class."""

    def test_admin_can_edit(self, org_admin):
        """ORG_ADMIN can edit."""
        factory = APIRequestFactory()
        request = factory.put('/api/projects/1/')

        user, org = org_admin
        project = Project.objects.create(name='Test', org=org)

        request.user = user
        permission = CanEditProject()
        assert permission.has_object_permission(request, None, project) is True

    def test_pi_can_edit(self, pi_user):
        """PI can edit."""
        factory = APIRequestFactory()
        request = factory.put('/api/projects/1/')

        user, org = pi_user
        project = Project.objects.create(name='Test', org=org)

        request.user = user
        permission = CanEditProject()
        assert permission.has_object_permission(request, None, project) is True

    def test_readonly_cannot_edit(self, readonly_user):
        """READ_ONLY cannot edit."""
        factory = APIRequestFactory()
        request = factory.put('/api/projects/1/')

        user, org = readonly_user
        project = Project.objects.create(name='Test', org=org)

        request.user = user
        permission = CanEditProject()
        assert permission.has_object_permission(request, None, project) is False

    def test_outsider_cannot_edit(self, org_admin, outsider_user):
        """Outsider cannot edit."""
        factory = APIRequestFactory()
        request = factory.put('/api/projects/1/')

        _, org = org_admin
        project = Project.objects.create(name='Test', org=org)

        request.user = outsider_user
        permission = CanEditProject()
        assert permission.has_object_permission(request, None, project) is False


@pytest.mark.django_db
class TestCanDeleteProjectPermission:
    """Test CanDeleteProject permission class."""

    def test_only_admin_can_delete(self, org_admin, pi_user, readonly_user):
        """Only ORG_ADMIN can delete."""
        factory = APIRequestFactory()
        request = factory.delete('/api/projects/1/')

        user_admin, org = org_admin
        project = Project.objects.create(name='Test', org=org)

        # ORG_ADMIN can delete
        request.user = user_admin
        permission = CanDeleteProject()
        assert permission.has_object_permission(request, None, project) is True

        # PI cannot delete
        request.user = pi_user[0]
        assert permission.has_object_permission(request, None, project) is False

        # READ_ONLY cannot delete
        request.user = readonly_user[0]
        assert permission.has_object_permission(request, None, project) is False

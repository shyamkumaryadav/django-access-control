"""

Tests for RBAC models.

Reference: LR5 - Building the Django Models

Reference: Phase 1 in plan.md

"""

import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError

from core.models import Org, Project, UserOrgRole


@pytest.mark.django_db
class TestOrgModel:
    """Test Org model and constraints."""

    def test_org_creation(self):
        """Test basic org creation."""

        user = User.objects.create_user("admin", "admin@test.com", "pass")

        org = Org.objects.create(name="Test Org", slug="test", admin=user)

        assert org.name == "Test Org"

        assert org.admin == user

        assert org.slug == "test"

    def test_org_slug_unique(self):
        """Test that org slugs must be unique."""

        user = User.objects.create_user("admin", "admin@test.com", "pass")

        Org.objects.create(name="Org 1", slug="test", admin=user)

        with pytest.raises(IntegrityError):

            Org.objects.create(name="Org 2", slug="test", admin=user)

    def test_org_admin_cannot_be_deleted(self):
        """Test that org admin user cannot be deleted."""

        user = User.objects.create_user("admin", "admin@test.com", "pass")

        Org.objects.create(name="Test Org", slug="test", admin=user)

        with pytest.raises(IntegrityError):

            user.delete()

    def test_org_string_representation(self):
        """Test org __str__ method."""

        user = User.objects.create_user("admin", "admin@test.com", "pass")

        org = Org.objects.create(name="ACME", slug="acme", admin=user)

        assert str(org) == "ACME (Admin: admin)"


@pytest.mark.django_db
class TestUserOrgRole:
    """Test UserOrgRole model."""

    def test_role_creation(self):
        """Test basic role creation."""

        user = User.objects.create_user("user1", "user1@test.com", "pass")

        admin = User.objects.create_user("admin", "admin@test.com", "pass")

        org = Org.objects.create(name="Test Org", slug="test", admin=admin)

        role = UserOrgRole.objects.create(user=user, org=org, role="PI")

        assert role.user == user

        assert role.org == org

        assert role.role == "PI"

    def test_unique_role_per_org(self):
        """Test that user can only have one role per org."""

        user = User.objects.create_user("user1", "user1@test.com", "pass")

        admin = User.objects.create_user("admin", "admin@test.com", "pass")

        org = Org.objects.create(name="Test Org", slug="test", admin=admin)

        UserOrgRole.objects.create(user=user, org=org, role="PI")

        with pytest.raises(IntegrityError):

            UserOrgRole.objects.create(user=user, org=org, role="READ_ONLY")

    def test_same_user_different_orgs(self):
        """Test that user can have different roles in different orgs."""

        user = User.objects.create_user("user1", "user1@test.com", "pass")

        admin1 = User.objects.create_user("admin1", "admin1@test.com", "pass")

        admin2 = User.objects.create_user("admin2", "admin2@test.com", "pass")

        org1 = Org.objects.create(name="Org 1", slug="org1", admin=admin1)

        org2 = Org.objects.create(name="Org 2", slug="org2", admin=admin2)

        role1 = UserOrgRole.objects.create(user=user, org=org1, role="PI")

        role2 = UserOrgRole.objects.create(user=user, org=org2, role="READ_ONLY")

        assert role1.role == "PI"

        assert role2.role == "READ_ONLY"


@pytest.mark.django_db
class TestProjectModel:
    """Test Project model."""

    def test_project_creation(self):
        """Test basic project creation."""

        admin = User.objects.create_user("admin", "admin@test.com", "pass")

        org = Org.objects.create(name="Test Org", slug="test", admin=admin)

        project = Project.objects.create(
            name="Project A", org=org, description="Test project"
        )

        assert project.name == "Project A"

        assert project.org == org

    def test_unique_project_name_per_org(self):
        """Test that project names must be unique within an org."""

        admin = User.objects.create_user("admin", "admin@test.com", "pass")

        org = Org.objects.create(name="Test Org", slug="test", admin=admin)

        Project.objects.create(name="Project A", org=org)

        with pytest.raises(IntegrityError):

            Project.objects.create(name="Project A", org=org)

    def test_same_project_name_different_orgs(self):
        """Test that same project name can exist in different orgs."""

        admin1 = User.objects.create_user("admin1", "admin1@test.com", "pass")

        admin2 = User.objects.create_user("admin2", "admin2@test.com", "pass")

        org1 = Org.objects.create(name="Org 1", slug="org1", admin=admin1)

        org2 = Org.objects.create(name="Org 2", slug="org2", admin=admin2)

        proj1 = Project.objects.create(name="Project A", org=org1)

        proj2 = Project.objects.create(name="Project A", org=org2)

        assert proj1.org == org1

        assert proj2.org == org2

"""
Pytest configuration for RBAC tests.
Reference: LR7 - Testing Permission Logic Comprehensively
"""
import os
import django
import pytest
from django.contrib.auth.models import User
from core.models import Org, UserOrgRole, Project

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


@pytest.fixture
def admin_user():
    """Create a superuser."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='admin123'
    )


@pytest.fixture
def org_admin(db):
    """Create an organization and its admin (ORG_ADMIN is not in UserOrgRole).
    Reference: LR2 - ORG_ADMIN is stored in Org.admin, not as a role
    """
    user = User.objects.create_user(
        username='org_admin@acme.com',
        email='org_admin@acme.com',
        password='password123'
    )
    org = Org.objects.create(
        name='ACME Corp',
        slug='acme',
        admin=user
    )
    # No UserOrgRole needed for org admin - they are identified via org.admin
    return user, org


@pytest.fixture
def pi_user(db, org_admin):
    """Create a PI user in the admin's org."""
    _, org = org_admin
    user = User.objects.create_user(
        username='pi@acme.com',
        email='pi@acme.com',
        password='password123'
    )
    UserOrgRole.objects.create(user=user, org=org, role='PI')
    return user, org


@pytest.fixture
def readonly_user(db, org_admin):
    """Create a read-only user in the admin's org."""
    _, org = org_admin
    user = User.objects.create_user(
        username='readonly@acme.com',
        email='readonly@acme.com',
        password='password123'
    )
    UserOrgRole.objects.create(user=user, org=org, role='READ_ONLY')
    return user, org


@pytest.fixture
def outsider_user(db):
    """Create a user with no org membership."""
    return User.objects.create_user(
        username='outsider@test.com',
        email='outsider@test.com',
        password='password123'
    )


@pytest.fixture
def project(db, org_admin):
    """Create a project in org_admin's org."""
    _, org = org_admin
    return Project.objects.create(
        name='Test Project',
        org=org,
        description='A test project'
    )

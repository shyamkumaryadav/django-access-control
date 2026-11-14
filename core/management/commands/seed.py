"""

Management command to seed database with test data.

Usage: python manage.py seed

"""

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand

from core.models import Org, Project, UserOrgRole


class Command(BaseCommand):

    help = "Delete database, run migrations, and populate with test data"

    def handle(self, *args, **options):

        self.stdout.write(self.style.WARNING("[*] Deleting database..."))
        # First run migrations to create tables
        self.stdout.write(self.style.WARNING("[*] Running migrations..."))
        call_command("migrate", verbosity=0)
        self.stdout.write(self.style.SUCCESS("[OK] Migrations complete"))
        # Now delete all data (respecting constraints)
        self.stdout.write(self.style.WARNING("[*] Clearing existing data..."))
        UserOrgRole.objects.all().delete()
        Project.objects.all().delete()
        Org.objects.all().delete()
        User.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("[OK] Database cleared"))
        # Create users
        self.stdout.write(self.style.WARNING("[*] Creating users..."))
        # Superusers
        User.objects.create_superuser(
            username="superuser1",
            email="superuser1@test.com",
            password="password123",
        )
        User.objects.create_superuser(
            username="superuser2",
            email="superuser2@test.com",
            password="password123",
        )
        self.stdout.write("  [OK] Created 2 superusers")

        # Regular users (org admins, PI, readonly)

        org_admin1 = User.objects.create_user(
            username="admin1@acme.com",
            email="admin1@acme.com",
            password="password123",
        )
        org_admin2 = User.objects.create_user(
            username="admin2@globex.com",
            email="admin2@globex.com",
            password="password123",
        )
        self.stdout.write("  [OK] Created 2 org admins")

        pi1_org1 = User.objects.create_user(
            username="pi1_acme@test.com",
            email="pi1_acme@test.com",
            password="password123",
        )
        pi1_org2 = User.objects.create_user(
            username="pi1_globex@test.com",
            email="pi1_globex@test.com",
            password="password123",
        )
        self.stdout.write("  [OK] Created 2 PI users")

        readonly1 = User.objects.create_user(
            username="readonly1@acme.com",
            email="readonly1@acme.com",
            password="password123",
        )
        readonly2 = User.objects.create_user(
            username="readonly2@globex.com",
            email="readonly2@globex.com",
            password="password123",
        )
        self.stdout.write("  [OK] Created 2 readonly users")

        # Create organizations
        self.stdout.write(self.style.WARNING("[*] Creating organizations..."))
        org1 = Org.objects.create(
            name="ACME Corp",
            slug="acme",
            admin=org_admin1,
        )
        org2 = Org.objects.create(
            name="Globex Corp",
            slug="globex",
            admin=org_admin2,
        )
        self.stdout.write("  [OK] Created 2 organizations")

        # Create UserOrgRoles (PI and ReadOnly for each org)
        self.stdout.write(self.style.WARNING("[*] Creating user org roles..."))

        # Org 1 roles
        UserOrgRole.objects.create(user=pi1_org1, org=org1, role="PI")
        UserOrgRole.objects.create(user=readonly1, org=org1, role="READ_ONLY")

        # Org 2 roles
        UserOrgRole.objects.create(user=pi1_org2, org=org2, role="PI")
        UserOrgRole.objects.create(user=readonly2, org=org2, role="READ_ONLY")
        self.stdout.write("  [OK] Created 4 user org roles")

        # Create projects
        self.stdout.write(self.style.WARNING("[*] Creating projects..."))

        # Org 1 projects
        Project.objects.create(
            name="Portal Dev",
            org=org1,
            description="Internal portal development",
        )
        Project.objects.create(
            name="API Gateway",
            org=org1,
            description="RESTful API gateway",
        )

        # Org 2 projects
        Project.objects.create(
            name="Analytics Platform",
            org=org2,
            description="Real-time analytics platform",
        )
        Project.objects.create(
            name="ML Pipeline",
            org=org2,
            description="Machine learning pipeline",
        )
        self.stdout.write("  [OK] Created 4 projects")

        # Print summary
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("[OK] DATABASE SEEDING COMPLETE"))
        self.stdout.write("=" * 70 + "\n")
        self.stdout.write(self.style.WARNING("[INFO] DATA SUMMARY"))
        self.stdout.write("-" * 70)
        self.stdout.write("Superusers:       2  [password123]")
        self.stdout.write("  - superuser1")
        self.stdout.write("  - superuser2")
        self.stdout.write("\nOrganization Admins: 2")
        self.stdout.write("  - admin1@acme.com -> ACME Corp")
        self.stdout.write("  - admin2@globex.com -> Globex Corp")
        self.stdout.write("\nPI Users:         2")
        self.stdout.write("  - pi1_acme@test.com -> ACME Corp")
        self.stdout.write("  - pi1_globex@test.com -> Globex Corp")
        self.stdout.write("\nReadOnly Users:   2")
        self.stdout.write("  - readonly1@acme.com -> ACME Corp")
        self.stdout.write("  - readonly2@globex.com -> Globex Corp")
        self.stdout.write("\nOrganizations:    2")
        self.stdout.write("  - ACME Corp (slug: acme)")
        self.stdout.write("  - Globex Corp (slug: globex)")
        self.stdout.write("\nProjects:         4 (2 per org)")
        self.stdout.write("  ACME:   Portal Dev, API Gateway")
        self.stdout.write("  Globex: Analytics Platform, ML Pipeline")
        self.stdout.write("\nUserOrgRoles:     4")
        self.stdout.write("  - ACME: 1 PI + 1 ReadOnly")
        self.stdout.write("  - Globex: 1 PI + 1 ReadOnly")
        self.stdout.write("-" * 70)
        self.stdout.write(self.style.WARNING("\n[INFO] ENDPOINTS"))
        self.stdout.write("-" * 70)

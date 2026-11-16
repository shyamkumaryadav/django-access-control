"""Seed readable accounts and organizations for manual RBAC testing."""

from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.urls import reverse

from core.models import Org, Project, UserOrgRole
from core.utils import ROLE_ADMIN, ROLE_PI, ROLE_READ_ONLY, ROLE_SI

# Each tester exercises every org role, plus no membership.
# slug, name, tester1 role, tester2 role, project count
SCENARIOS = [
    ("admin-one", "Admin One Demo", ROLE_ADMIN, ROLE_PI, 2),
    ("admin-two", "Admin Two Demo", ROLE_PI, ROLE_ADMIN, 2),
    ("viewer", "Viewer Demo", ROLE_READ_ONLY, ROLE_SI, 2),
    ("integrator", "Integrator Demo", ROLE_SI, ROLE_READ_ONLY, 2),
    ("private", "Private Demo", None, None, 2),
    ("empty", "Empty Demo", ROLE_PI, ROLE_READ_ONLY, 0),
]


class Command(BaseCommand):
    help = "Delete the SQLite database file, run migrations, and seed RBAC demo data"

    def handle(self, *args, **options):
        database_name = str(connection.settings_dict["NAME"])
        if (
            connection.vendor != "sqlite"
            or database_name == ":memory:"
            or database_name.startswith("file:")
            or not database_name
        ):
            raise CommandError("This command requires a file-based SQLite database.")
        database_path = Path(database_name).resolve()
        connection.close()
        self.stdout.write(f"Deleting SQLite database: {database_path}")
        try:
            database_path.unlink(missing_ok=True)
        except OSError as error:
            raise CommandError(f"Could not delete {database_path}: {error}") from error
        self.stdout.write("Running migrations...")
        call_command("migrate", verbosity=0)
        self.stdout.write("Creating demo data...")
        with transaction.atomic():
            for number in (1, 2):
                self.create_user(f"superuser{number}", is_superuser=True, is_staff=True)
                self.create_user(f"outsider{number}")

            testers = [self.create_user(f"tester{number}") for number in (1, 2)]
            summary = []
            for slug, name, role1, role2, project_count in SCENARIOS:
                roles = (role1, role2)
                admin = next(
                    (user for user, role in zip(testers, roles) if role == ROLE_ADMIN),
                    None,
                )
                if admin is None:
                    admin = self.create_user(f"admin_{slug}")
                org = Org.objects.create(name=name, slug=slug, admin=admin)
                for user, role in zip(testers, roles):
                    if role and role != ROLE_ADMIN:
                        UserOrgRole.objects.create(user=user, org=org, role=role)
                for number in range(1, project_count + 1):
                    # Repeated names across orgs exercise tenant isolation.
                    Project.objects.create(
                        org=org,
                        name=f"Project {number}",
                        description=(
                            f"Demo project in {name}.\nUse for edit/delete checks."
                            if number == 1
                            else ""
                        ),
                    )
                summary.append((org, roles))

        self.stdout.write(self.style.SUCCESS("Seeding complete. Password: password123"))
        self.stdout.write("\nMain accounts: tester1, tester2")
        self.stdout.write(f"{'Organization':<22} {'tester1':<12} {'tester2':<12} Admin")
        for org, roles in summary:
            self.stdout.write(
                f"{org.name:<22} {roles[0] or 'NO ACCESS':<12} "
                f"{roles[1] or 'NO ACCESS':<12} {org.admin.username}"
            )
            self.stdout.write(
                "  "
                + reverse("org-detail", args=[org.pk])
                + "  "
                + reverse("org-projects-list", kwargs={"org_id": org.pk})
            )
        self.stdout.write(
            "\nsuperuser1 / superuser2: full access to every organization."
        )
        self.stdout.write("outsider1 / outsider2: no organizations or project access.")
        self.stdout.write("admin_*: supporting admins, access only to their own org.")
        self.stdout.write("Empty Demo has no projects; other orgs have two each.")
        self.stdout.write(
            f"Totals: {User.objects.count()} users, {Org.objects.count()} orgs, "
            f"{UserOrgRole.objects.count()} memberships, "
            f"{Project.objects.count()} projects."
        )

    def create_user(self, username, **flags):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="password123",
            **flags,
        )

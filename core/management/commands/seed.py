"""
Management command to seed database with test data.
Usage: python manage.py seed
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from core.models import Org, UserOrgRole, Project


class Command(BaseCommand):
    help = 'Delete database, run migrations, and populate with test data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('[*] Deleting database...'))
        
        # First run migrations to create tables
        self.stdout.write(self.style.WARNING('[*] Running migrations...'))
        call_command('migrate', verbosity=0)
        self.stdout.write(self.style.SUCCESS('[OK] Migrations complete'))
        
        # Now delete all data (respecting constraints)
        self.stdout.write(self.style.WARNING('[*] Clearing existing data...'))
        UserOrgRole.objects.all().delete()
        Project.objects.all().delete()
        Org.objects.all().delete()
        User.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('[OK] Database cleared'))

        # Create users
        self.stdout.write(self.style.WARNING('[*] Creating users...'))
        
        # Superusers
        superuser1 = User.objects.create_superuser(
            username='superuser1',
            email='superuser1@test.com',
            password='password123'
        )
        superuser2 = User.objects.create_superuser(
            username='superuser2',
            email='superuser2@test.com',
            password='password123'
        )
        self.stdout.write(f'  [OK] Created 2 superusers')
        
        # Regular users (org admins, PI, readonly)
        org_admin1 = User.objects.create_user(
            username='admin1@acme.com',
            email='admin1@acme.com',
            password='password123'
        )
        org_admin2 = User.objects.create_user(
            username='admin2@globex.com',
            email='admin2@globex.com',
            password='password123'
        )
        self.stdout.write(f'  [OK] Created 2 org admins')
        
        pi1_org1 = User.objects.create_user(
            username='pi1_acme@test.com',
            email='pi1_acme@test.com',
            password='password123'
        )
        pi1_org2 = User.objects.create_user(
            username='pi1_globex@test.com',
            email='pi1_globex@test.com',
            password='password123'
        )
        self.stdout.write(f'  [OK] Created 2 PI users')
        
        readonly1 = User.objects.create_user(
            username='readonly1@acme.com',
            email='readonly1@acme.com',
            password='password123'
        )
        readonly2 = User.objects.create_user(
            username='readonly2@globex.com',
            email='readonly2@globex.com',
            password='password123'
        )
        self.stdout.write(f'  [OK] Created 2 readonly users')

        # Create organizations
        self.stdout.write(self.style.WARNING('[*] Creating organizations...'))
        
        org1 = Org.objects.create(
            name='ACME Corp',
            slug='acme',
            admin=org_admin1
        )
        org2 = Org.objects.create(
            name='Globex Corp',
            slug='globex',
            admin=org_admin2
        )
        self.stdout.write(f'  [OK] Created 2 organizations')

        # Create UserOrgRoles (PI and ReadOnly for each org)
        self.stdout.write(self.style.WARNING('[*] Creating user org roles...'))
        
        # Org 1 roles
        UserOrgRole.objects.create(user=pi1_org1, org=org1, role='PI')
        UserOrgRole.objects.create(user=readonly1, org=org1, role='READ_ONLY')
        
        # Org 2 roles
        UserOrgRole.objects.create(user=pi1_org2, org=org2, role='PI')
        UserOrgRole.objects.create(user=readonly2, org=org2, role='READ_ONLY')
        
        self.stdout.write(f'  [OK] Created 4 user org roles')

        # Create projects
        self.stdout.write(self.style.WARNING('[*] Creating projects...'))
        
        # Org 1 projects
        project1_org1 = Project.objects.create(
            name='Portal Dev',
            org=org1,
            description='Internal portal development'
        )
        project2_org1 = Project.objects.create(
            name='API Gateway',
            org=org1,
            description='RESTful API gateway'
        )
        
        # Org 2 projects
        project1_org2 = Project.objects.create(
            name='Analytics Platform',
            org=org2,
            description='Real-time analytics platform'
        )
        project2_org2 = Project.objects.create(
            name='ML Pipeline',
            org=org2,
            description='Machine learning pipeline'
        )
        
        self.stdout.write(f'  [OK] Created 4 projects')

        # Print summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('[OK] DATABASE SEEDING COMPLETE'))
        self.stdout.write('=' * 70 + '\n')
        
        self.stdout.write(self.style.WARNING('[INFO] DATA SUMMARY'))
        self.stdout.write('-' * 70)
        self.stdout.write(f'Superusers:       2')
        self.stdout.write(f'  - superuser1 (password123)')
        self.stdout.write(f'  - superuser2 (password123)')
        self.stdout.write(f'\nOrganization Admins: 2')
        self.stdout.write(f'  - admin1@acme.com -> ACME Corp (password123)')
        self.stdout.write(f'  - admin2@globex.com -> Globex Corp (password123)')
        self.stdout.write(f'\nPI Users:         2')
        self.stdout.write(f'  - pi1_acme@test.com -> ACME Corp (password123)')
        self.stdout.write(f'  - pi1_globex@test.com -> Globex Corp (password123)')
        self.stdout.write(f'\nReadOnly Users:   2')
        self.stdout.write(f'  - readonly1@acme.com -> ACME Corp (password123)')
        self.stdout.write(f'  - readonly2@globex.com -> Globex Corp (password123)')
        self.stdout.write(f'\nOrganizations:    2')
        self.stdout.write(f'  - ACME Corp (slug: acme)')
        self.stdout.write(f'  - Globex Corp (slug: globex)')
        self.stdout.write(f'\nProjects:         4 (2 per org)')
        self.stdout.write(f'  ACME:   Portal Dev, API Gateway')
        self.stdout.write(f'  Globex: Analytics Platform, ML Pipeline')
        self.stdout.write(f'\nUserOrgRoles:     4')
        self.stdout.write(f'  - ACME: 1 PI + 1 ReadOnly')
        self.stdout.write(f'  - Globex: 1 PI + 1 ReadOnly')
        self.stdout.write('-' * 70)
        
        self.stdout.write(self.style.WARNING('\n[INFO] ENDPOINTS'))
        self.stdout.write('-' * 70)
        self.stdout.write('API:               http://localhost:8000/api/')
        self.stdout.write('Orgs List:         http://localhost:8000/api/orgs/')
        self.stdout.write('Projects List:     http://localhost:8000/api/projects/')
        self.stdout.write('Fake Login:        http://localhost:8000/api/fake-login/')
        self.stdout.write('Django Admin:      http://localhost:8000/admin/')
        self.stdout.write('-' * 70 + '\n')

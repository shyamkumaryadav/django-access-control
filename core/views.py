from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Org, UserOrgRole, Project
from .serializers import (
    OrgSerializer,
    ProjectSerializer,
    FakeLoginSerializer,
)
from .permissions import RolePermission


class OrgViewSet(viewsets.ModelViewSet):
    serializer_class = OrgSerializer
    permission_classes = [RolePermission,]
    queryset = (
        Org.objects
        .select_related("admin")
        .prefetch_related("user_roles")
        .all()
    )

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_superuser:
            return queryset

        return (
            queryset
            .filter(
                Q(admin=user) |
                Q(user_roles__user=user)
            )
            .distinct()
        )


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = (
        Project.objects
        .select_related("org", "org__admin")
        .all()
    )
    serializer_class = ProjectSerializer
    permission_classes = [RolePermission]

    def get_queryset(self):
        org_id = self.kwargs["org_id"]

        return (
            super()
            .get_queryset()
            .filter(org_id=org_id)
        )

    def perform_create(self, serializer):
        org_id = self.kwargs["org_id"]
        serializer.save(org_id=org_id)


class FakeLoginView(CreateAPIView):
    """
    Fake login endpoint for development - switch between test users.
    
    Provides browsable API form with user dropdown selector.
    All subsequent requests will use the selected user context.
    
    GET: Display the login form
    POST: Switch to selected user (store in session)
    
    Test Users:
    - Superusers: superuser1, superuser2 (access all)
    - Org Admins: admin1@acme.com, admin2@globex.com (control 1 org)
    - PI Users: pi1_acme@test.com, pi1_globex@test.com (edit projects)
    - ReadOnly: readonly1@acme.com, readonly2@globex.com (view only)
    
    All passwords: password123
    """
    permission_classes = [AllowAny]
    serializer_class = FakeLoginSerializer

    def create(self, request, *args, **kwargs):
        """POST: Switch to selected user (store in session)."""
        # Validate using serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract user ID from validated data
        user_id = serializer.validated_data['user_id']
        user = User.objects.get(id=user_id)
        
        # Store user ID in session
        request.session['_fake_user_id'] = user_id
        request.session.save()
        
        # Get user details
        is_superuser = user.is_superuser
        roles = UserOrgRole.objects.filter(user=user).select_related('org')
        role_list = [
            {
                'role': role.get_role_display(),
                'organization': role.org.name
            }
            for role in roles
        ]
        
        # Check if org admin
        admin_orgs = Org.objects.filter(admin=user)
        if admin_orgs.exists():
            for org in admin_orgs:
                role_list.insert(0, {
                    'role': 'Org Admin',
                    'organization': org.name
                })
        
        return Response({
            'success': True,
            'message': f'Successfully logged in as {user.get_full_name() or user.username}',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'is_superuser': is_superuser,
                'type': 'Superuser' if is_superuser else 'Regular User',
                'roles': role_list if role_list else []
            },
            'next_steps': [
                f'You are now logged in as {user.username}',
                'Visit /api/orgs/ or /api/projects/ to see your data',
                'Use fake-login again to switch to another user',
                'Your session will persist across requests'
            ]
        }, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        """GET: Display login form with user list info."""
        all_users = User.objects.all().order_by('is_superuser', 'username')
        
        # Build user list with roles
        user_list = []
        for user in all_users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
                'type': 'Superuser' if user.is_superuser else 'Regular User'
            }
            
            # Add org roles if any
            roles = UserOrgRole.objects.filter(user=user).select_related('org')
            if roles.exists():
                user_data['roles'] = [
                    f"{role.get_role_display()} - {role.org.name}"
                    for role in roles
                ]
            else:
                # Check if org admin
                admin_orgs = Org.objects.filter(admin=user)
                if admin_orgs.exists():
                    user_data['roles'] = [
                        f"Org Admin - {org.name}"
                        for org in admin_orgs
                    ]
            
            user_list.append(user_data)
        
        return Response({
            'message': 'Select a user to fake login',
            'current_user': {
                'id': request.user.id if request.user.is_authenticated else None,
                'username': request.user.username if request.user.is_authenticated else 'Anonymous'
            },
            'users': user_list,
            'instructions': [
                'Select a user from the dropdown and click POST',
                'All subsequent requests will use this user',
                'Visit /api/orgs/ or /api/projects/ to test access control'
            ]
        })


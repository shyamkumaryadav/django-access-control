from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Org, Project
from .permissions import RolePermission
from .serializers import FakeLoginSerializer, OrgSerializer, ProjectSerializer, UserListSerializer


class OrgViewSet(viewsets.ModelViewSet):

    serializer_class = OrgSerializer

    permission_classes = [
        RolePermission,
    ]

    queryset = (
        Org.objects.select_related("admin")
        .prefetch_related(
            "user_roles",
        )
        .all()
    )

    def get_queryset(self):

        user = self.request.user

        queryset = super().get_queryset()

        if user.is_superuser:

            return queryset

        return queryset.filter(
            Q(admin=user) | Q(user_roles__user=user),
        ).distinct()


class ProjectViewSet(viewsets.ModelViewSet):

    queryset = Project.objects.select_related("org", "org__admin").all()

    serializer_class = ProjectSerializer

    permission_classes = [RolePermission]

    def get_queryset(self):

        org_id = self.kwargs["org_id"]

        return super().get_queryset().filter(org_id=org_id)

    def perform_create(self, serializer):

        org_id = self.kwargs["org_id"]

        serializer.save(org_id=org_id)


class FakeLoginView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [AllowAny]
    queryset = User.objects.all().order_by("username")

    def get_serializer_class(self):
        if self.action == "list":
            return UserListSerializer
        return FakeLoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user_id"]

        login(
            request,
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )

        return Response(
            {
                "success": True,
                "message": f"Logged in as {user.username}",
            }
        )

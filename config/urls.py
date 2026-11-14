from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.views import FakeLoginView, OrgViewSet, ProjectViewSet

# Main router for organizations

router = DefaultRouter()

router.register(r"orgs", OrgViewSet, basename="org")

router.register(r"orgs/(?P<org_id>\d+)/projects", ProjectViewSet, basename="org-projects")

router.register("fake-login", FakeLoginView, basename="fake-login")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
]


# Django Debug Toolbar URLs

if settings.DEBUG:

    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
        *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    ]

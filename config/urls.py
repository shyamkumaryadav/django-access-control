"""
URL configuration for RBAC project.
Reference: LR3 - Permission Routing & Querysets

Nested routing:
  /api/orgs/ - List/create organizations
  /api/orgs/{org_id}/ - Retrieve/update/delete organization
  /api/orgs/{org_id}/projects/ - List/create projects in org
  /api/orgs/{org_id}/projects/{project_id}/ - Retrieve/update/delete project
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from core.views import OrgViewSet, ProjectViewSet, FakeLoginView

# Main router for organizations
router = DefaultRouter()
router.register(r'orgs', OrgViewSet, basename='org')
router.register(r'orgs/(?P<org_id>\d+)/projects', ProjectViewSet, basename='org-projects')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/fake-login/', FakeLoginView.as_view(), name='fake-login'),
    path('api-auth/', include('rest_framework.urls')),
]

# Django Debug Toolbar URLs
if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]

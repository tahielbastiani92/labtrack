from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from apps.projects.api import ProjectMembershipViewSet, ProjectViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")
router.register("memberships", ProjectMembershipViewSet, basename="membership")

urlpatterns = [
    path("auth/token/", obtain_auth_token, name="api_token"),
    path("", include(router.urls)),
]

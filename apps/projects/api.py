from rest_framework import mixins, serializers, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from config.utils import parse_uuid

from .access import can_manage_project, get_visible_project, projects_visible_to
from .models import Project, ProjectMembership
from .serializers import ProjectMembershipSerializer, ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        queryset = projects_visible_to(self.request.user).select_related("created_by")
        query = self.request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        status = self.request.query_params.get("status", "")
        if status in Project.Status.values:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_object(self):
        project = super().get_object()
        if self.action in ("update", "partial_update", "destroy") and not can_manage_project(
            self.request.user, project
        ):
            raise PermissionDenied(
                "Only the project creator or an administrator can manage this project."
            )
        return project

    def perform_destroy(self, instance):
        if instance.samples.exists() or instance.datasets.exists():
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Delete the project's samples and datasets before deleting the project."
                    )
                }
            )
        instance.delete()


class ProjectMembershipViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ProjectMembershipSerializer

    def get_queryset(self):
        queryset = (
            ProjectMembership.objects.filter(
                project__in=projects_visible_to(self.request.user)
            )
            .select_related("project", "user")
            .order_by("project__name", "joined_at")
        )
        raw_project = self.request.query_params.get("project")
        if raw_project:
            project_id = parse_uuid(raw_project)
            if project_id is None:
                raise ValidationError({"project": "Invalid project identifier."})
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def create(self, request, *args, **kwargs):
        project_id = parse_uuid(request.data.get("project"))
        if project_id is None:
            raise ValidationError({"project": "Invalid project identifier."})
        project = get_visible_project(request.user, project_id)
        if not can_manage_project(request.user, project):
            raise PermissionDenied(
                "Only the project creator or an administrator can manage membership."
            )
        return super().create(request, *args, **kwargs)

    def get_object(self):
        membership = super().get_object()
        if not can_manage_project(self.request.user, membership.project):
            raise PermissionDenied(
                "Only the project creator or an administrator can manage membership."
            )
        return membership

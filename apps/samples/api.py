from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.projects.access import project_is_writable
from config.utils import parse_uuid

from .models import Sample
from .selectors import samples_visible_to
from .serializers import SampleSerializer


class SampleViewSet(viewsets.ModelViewSet):
    serializer_class = SampleSerializer

    def get_queryset(self):
        queryset = samples_visible_to(self.request.user).select_related(
            "project", "created_by"
        )
        query = self.request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(code__icontains=query)
        sample_type = self.request.query_params.get("type", "").strip()
        if sample_type:
            queryset = queryset.filter(sample_type__icontains=sample_type)
        status = self.request.query_params.get("status", "")
        if status in Sample.Status.values:
            queryset = queryset.filter(status=status)
        raw_project = self.request.query_params.get("project")
        if raw_project:
            project_id = parse_uuid(raw_project)
            if project_id is None:
                raise ValidationError({"project": "Invalid project identifier."})
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def get_object(self):
        sample = super().get_object()
        if self.action in ("update", "partial_update", "destroy") and not project_is_writable(
            sample.project
        ):
            raise PermissionDenied("Archived projects are read-only.")
        return sample

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

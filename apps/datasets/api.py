from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.projects.access import project_is_writable
from config.utils import parse_uuid

from .models import Dataset
from .selectors import datasets_visible_to
from .serializers import DatasetSerializer


class DatasetViewSet(viewsets.ModelViewSet):
    serializer_class = DatasetSerializer

    def get_queryset(self):
        queryset = (
            datasets_visible_to(self.request.user)
            .select_related("project", "created_by")
            .prefetch_related("samples")
        )
        query = self.request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        data_format = self.request.query_params.get("data_format", "")
        if data_format in Dataset.DataFormat.values:
            queryset = queryset.filter(data_format=data_format)
        raw_project = self.request.query_params.get("project")
        if raw_project:
            project_id = parse_uuid(raw_project)
            if project_id is None:
                raise ValidationError({"project": "Invalid project identifier."})
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def get_object(self):
        dataset = super().get_object()
        if self.action in ("update", "partial_update", "destroy") and not project_is_writable(
            dataset.project
        ):
            raise PermissionDenied("Archived projects are read-only.")
        return dataset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

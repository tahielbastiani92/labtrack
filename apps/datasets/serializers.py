from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.projects.access import project_is_writable, projects_visible_to
from apps.projects.models import Project
from apps.samples.models import Sample
from apps.samples.selectors import samples_visible_to

from .models import Dataset
from .rules import validate_samples_belong_to_project


class DatasetSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.none())
    samples = serializers.PrimaryKeyRelatedField(
        queryset=Sample.objects.none(),
        many=True,
        required=False,
    )
    created_by = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Dataset
        fields = (
            "id",
            "project",
            "name",
            "description",
            "data_format",
            "storage_uri",
            "samples",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            self.fields["project"].queryset = projects_visible_to(request.user)
            self.fields["samples"].child_relation.queryset = samples_visible_to(request.user)
        if self.instance is not None:
            self.fields["project"].read_only = True

    def validate_project(self, value):
        if not project_is_writable(value):
            raise serializers.ValidationError("Archived projects are read-only.")
        return value

    def validate(self, attrs):
        if self.instance is not None:
            project = self.instance.project
        else:
            project = attrs.get("project")
        if project is None:
            return attrs
        if not project_is_writable(project):
            raise serializers.ValidationError({"detail": "Archived projects are read-only."})

        samples = attrs.get("samples")
        if samples is not None:
            try:
                validate_samples_belong_to_project(project, samples)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"samples": exc.messages}) from exc
        return attrs

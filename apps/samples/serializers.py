from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from apps.projects.access import project_is_writable, projects_visible_to
from apps.projects.models import Project

from .models import Sample
from .rules import validate_status_transition


class SampleSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.none())
    created_by = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Sample
        fields = (
            "id",
            "project",
            "code",
            "sample_type",
            "collection_date",
            "status",
            "notes",
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
        if self.instance is not None:
            self.fields["project"].read_only = True
        else:
            self.fields["status"].read_only = True

    def validate_project(self, value):
        if not project_is_writable(value):
            raise serializers.ValidationError("Archived projects are read-only.")
        return value

    def validate_code(self, value):
        return value.strip().upper()

    def validate_collection_date(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError("Collection date cannot be in the future.")
        return value

    def validate_status(self, value):
        if self.instance is not None and value != self.instance.status:
            try:
                validate_status_transition(self.instance.status, value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages) from exc
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

        code = attrs.get("code", self.instance.code if self.instance is not None else None)
        if code:
            existing = Sample.objects.filter(project=project, code=code)
            if self.instance is not None:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    {"code": "A sample with this code already exists in the project."}
                )
        return attrs

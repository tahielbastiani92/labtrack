from django.contrib.auth import get_user_model
from rest_framework import serializers

from .access import projects_visible_to
from .models import Project, ProjectMembership

User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "description",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")


class ProjectMembershipSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.none())
    project_name = serializers.CharField(source="project.name", read_only=True)
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True)
    )
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ("id", "project", "project_name", "user", "username", "joined_at")
        read_only_fields = ("id", "project_name", "username", "joined_at")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            self.fields["project"].queryset = projects_visible_to(request.user)

    def validate(self, attrs):
        project = attrs.get("project")
        user = attrs.get("user")
        if project is not None and user is not None:
            if user.pk == project.created_by_id:
                raise serializers.ValidationError(
                    {"user": "The project creator already has access."}
                )
            if ProjectMembership.objects.filter(project=project, user=user).exists():
                raise serializers.ValidationError(
                    {"user": "This user is already a member of the project."}
                )
        return attrs

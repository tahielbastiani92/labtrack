from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Project


def projects_visible_to(user):
    if not user.is_authenticated:
        return Project.objects.none()
    if user.is_administrator:
        return Project.objects.all()
    return Project.objects.filter(
        Q(created_by=user) | Q(memberships__user=user)
    ).distinct()


def get_visible_project(user, pk):
    return get_object_or_404(projects_visible_to(user), pk=pk)


def can_manage_project(user, project) -> bool:
    return user.is_authenticated and (
        user.is_administrator or project.created_by_id == user.id
    )


def project_is_writable(project) -> bool:
    return project.status != Project.Status.ARCHIVED

from apps.projects.access import projects_visible_to

from .models import Dataset


def datasets_visible_to(user):
    return Dataset.objects.filter(project__in=projects_visible_to(user))

from apps.projects.access import projects_visible_to

from .models import Sample


def samples_visible_to(user):
    return Sample.objects.filter(project__in=projects_visible_to(user))

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.datasets.selectors import datasets_visible_to
from apps.projects.access import projects_visible_to
from apps.samples.selectors import samples_visible_to


@login_required
def dashboard(request):
    projects = projects_visible_to(request.user)
    samples = samples_visible_to(request.user)
    datasets = datasets_visible_to(request.user)

    context = {
        "project_count": projects.count(),
        "sample_count": samples.count(),
        "dataset_count": datasets.count(),
        "recent_projects": projects.select_related("created_by").order_by("-updated_at")[:5],
        "recent_samples": (
            samples.select_related("project", "created_by").order_by("-updated_at")[:5]
        ),
        "recent_datasets": (
            datasets.select_related("project", "created_by").order_by("-updated_at")[:5]
        ),
    }
    return render(request, "dashboard.html", context)

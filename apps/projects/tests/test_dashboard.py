import pytest
from django.urls import reverse

from apps.datasets.models import Dataset
from apps.projects.models import Project
from apps.samples.models import Sample


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    response = client.get(reverse("dashboard"))

    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_login_page_renders(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert b"Log in" in response.content


@pytest.mark.django_db
def test_login_redirects_to_dashboard(client, user):
    response = client.post(
        reverse("login"),
        {"username": user.username, "password": "test-password"},
    )

    assert response.status_code == 302
    assert response.url == reverse("dashboard")


@pytest.mark.django_db
def test_dashboard_counts_are_scoped_to_visible_projects(
    client, user, owned_project, sample, dataset, other_user
):
    other_project = Project.objects.create(name="Other project", created_by=other_user)
    Sample.objects.create(
        project=other_project,
        code="S-999",
        sample_type="blood",
        created_by=other_user,
    )
    Dataset.objects.create(
        project=other_project,
        name="Other dataset",
        created_by=other_user,
    )

    client.force_login(user)
    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert response.context["project_count"] == 1
    assert response.context["sample_count"] == 1
    assert response.context["dataset_count"] == 1

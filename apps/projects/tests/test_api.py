import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.projects.models import Project


@pytest.mark.django_db
def test_project_api_requires_authentication(api_client):
    response = api_client.get(reverse("project-list"))

    assert response.status_code in {401, 403}


@pytest.mark.django_db
def test_project_api_accepts_session_authentication(api_client, user, owned_project):
    assert api_client.login(username=user.username, password="test-password")

    response = api_client.get(reverse("project-list"))

    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_token_endpoint_and_token_authentication(api_client, user, owned_project):
    response = api_client.post(
        reverse("api_token"),
        {"username": user.username, "password": "test-password"},
        format="json",
    )

    assert response.status_code == 200
    token = response.data["token"]

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    response = client.get(reverse("project-list"))

    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_project_list_is_scoped_to_visible_projects(
    api_client, user, owned_project, joined_project, member_project
):
    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("project-list"))

    ids = {item["id"] for item in response.data["results"]}
    assert str(owned_project.pk) in ids
    assert str(joined_project.pk) in ids
    assert str(member_project.pk) not in ids


@pytest.mark.django_db
def test_administrator_sees_all_projects(api_client, admin_user, member_project):
    api_client.force_authenticate(user=admin_user)
    response = api_client.get(reverse("project-list"))

    ids = {item["id"] for item in response.data["results"]}
    assert str(member_project.pk) in ids


@pytest.mark.django_db
def test_inaccessible_project_detail_returns_not_found(api_client, user, member_project):
    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("project-detail", args=[member_project.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_project_create_sets_creator_from_request(api_client, user, other_user):
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("project-list"),
        {
            "name": "API project",
            "description": "Synthetic project",
            "status": Project.Status.ACTIVE,
            "created_by": other_user.pk,
        },
        format="json",
    )

    assert response.status_code == 201
    project = Project.objects.get(pk=response.data["id"])
    assert project.created_by == user


@pytest.mark.django_db
def test_project_update_requires_creator_or_administrator(
    api_client, user, admin_user, owned_project, joined_project, member_project
):
    api_client.force_authenticate(user=user)

    response = api_client.patch(
        reverse("project-detail", args=[joined_project.pk]),
        {"name": "Renamed"},
        format="json",
    )
    assert response.status_code == 403

    response = api_client.patch(
        reverse("project-detail", args=[owned_project.pk]),
        {"name": "Renamed"},
        format="json",
    )
    assert response.status_code == 200

    api_client.force_authenticate(user=admin_user)
    response = api_client.patch(
        reverse("project-detail", args=[member_project.pk]),
        {"name": "Renamed by administrator"},
        format="json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_project_delete_requires_empty_project(api_client, user, owned_project, sample):
    api_client.force_authenticate(user=user)

    response = api_client.delete(reverse("project-detail", args=[owned_project.pk]))
    assert response.status_code == 400

    empty_project = Project.objects.create(name="Empty project", created_by=user)
    response = api_client.delete(reverse("project-detail", args=[empty_project.pk]))
    assert response.status_code == 204


@pytest.mark.django_db
def test_project_list_paginates(api_client, user):
    for index in range(21):
        Project.objects.create(name=f"Project {index}", created_by=user)

    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("project-list"))

    assert response.data["count"] == 21
    assert len(response.data["results"]) == 20

    response = api_client.get(reverse("project-list"), {"page": 2})
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_project_list_filters(api_client, user, owned_project, joined_project):
    api_client.force_authenticate(user=user)

    response = api_client.get(reverse("project-list"), {"q": "Owned"})
    assert response.data["count"] == 1

    response = api_client.get(reverse("project-list"), {"status": Project.Status.ACTIVE})
    assert response.data["count"] == 2

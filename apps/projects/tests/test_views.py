import pytest
from django.urls import reverse

from apps.projects.models import Project, ProjectMembership


@pytest.mark.django_db
def test_project_list_requires_login(client):
    response = client.get(reverse("projects:list"))

    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_project_list_is_scoped_to_visible_projects(
    client, user, owned_project, joined_project, member_project
):
    client.force_login(user)
    response = client.get(reverse("projects:list"))

    names = {project.name for project in response.context["projects"]}
    assert names == {"Owned project", "Joined project"}


@pytest.mark.django_db
def test_project_list_paginates(client, user):
    for index in range(21):
        Project.objects.create(name=f"Project {index}", created_by=user)

    client.force_login(user)
    response = client.get(reverse("projects:list"))

    assert response.context["is_paginated"] is True
    assert len(response.context["projects"]) == 20

    response = client.get(reverse("projects:list"), {"page": 2})
    assert len(response.context["projects"]) == 1


@pytest.mark.django_db
def test_project_detail_is_hidden_from_non_members(client, user, member_project):
    client.force_login(user)
    response = client.get(reverse("projects:detail", args=[member_project.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_administrator_can_view_any_project(client, admin_user, member_project):
    client.force_login(admin_user)
    response = client.get(reverse("projects:detail", args=[member_project.pk]))

    assert response.status_code == 200


@pytest.mark.django_db
def test_project_create_sets_creator(client, user):
    client.force_login(user)
    response = client.post(
        reverse("projects:create"),
        {"name": "New project", "description": "Description", "status": "active"},
    )

    assert response.status_code == 302
    project = Project.objects.get(name="New project")
    assert project.created_by == user


@pytest.mark.django_db
def test_project_update_allowed_for_creator(client, user, owned_project):
    client.force_login(user)
    response = client.post(
        reverse("projects:update", args=[owned_project.pk]),
        {"name": "Updated project", "description": "", "status": "completed"},
    )

    assert response.status_code == 302
    owned_project.refresh_from_db()
    assert owned_project.name == "Updated project"
    assert owned_project.status == Project.Status.COMPLETED


@pytest.mark.django_db
def test_project_update_forbidden_for_member(client, member_user, member_project):
    client.force_login(member_user)
    response = client.post(
        reverse("projects:update", args=[member_project.pk]),
        {"name": "Hijacked", "description": "", "status": "active"},
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_project_delete_is_blocked_while_records_exist(client, user, owned_project, sample):
    client.force_login(user)
    response = client.post(reverse("projects:delete", args=[owned_project.pk]))

    assert response.status_code == 302
    assert Project.objects.filter(pk=owned_project.pk).exists()


@pytest.mark.django_db
def test_empty_project_can_be_deleted(client, user, owned_project):
    client.force_login(user)
    response = client.post(reverse("projects:delete", args=[owned_project.pk]))

    assert response.status_code == 302
    assert not Project.objects.filter(pk=owned_project.pk).exists()


@pytest.mark.django_db
def test_membership_can_be_added_and_removed(client, user, owned_project, member_user):
    client.force_login(user)
    response = client.post(
        reverse("projects:membership_add", args=[owned_project.pk]),
        {"user": member_user.pk},
    )

    assert response.status_code == 302
    membership = ProjectMembership.objects.get(project=owned_project, user=member_user)

    response = client.post(
        reverse(
            "projects:membership_remove",
            args=[owned_project.pk, membership.pk],
        )
    )

    assert response.status_code == 302
    assert not ProjectMembership.objects.filter(pk=membership.pk).exists()


@pytest.mark.django_db
def test_creator_cannot_be_added_as_member(client, user, owned_project):
    client.force_login(user)
    response = client.post(
        reverse("projects:membership_add", args=[owned_project.pk]),
        {"user": user.pk},
    )

    assert response.status_code == 302
    assert not ProjectMembership.objects.filter(
        project=owned_project, user=user
    ).exists()


@pytest.mark.django_db
def test_member_cannot_manage_membership(client, member_user, member_project, user):
    client.force_login(member_user)
    response = client.post(
        reverse("projects:membership_add", args=[member_project.pk]),
        {"user": user.pk},
    )

    assert response.status_code == 403

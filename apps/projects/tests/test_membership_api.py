import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.projects.models import Project, ProjectMembership


@pytest.mark.django_db
def test_membership_list_is_scoped_to_visible_projects(
    api_client, user, admin_user, joined_project, member_project
):
    user_membership = joined_project.memberships.get(user=user)
    hidden_membership = member_project.memberships.get()

    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("membership-list"))

    ids = {item["id"] for item in response.data["results"]}
    assert str(user_membership.pk) in ids
    assert str(hidden_membership.pk) not in ids

    api_client.force_authenticate(user=admin_user)
    response = api_client.get(reverse("membership-list"))

    ids = {item["id"] for item in response.data["results"]}
    assert str(hidden_membership.pk) in ids


@pytest.mark.django_db
def test_membership_list_filters_by_project(api_client, user, joined_project):
    api_client.force_authenticate(user=user)

    response = api_client.get(
        reverse("membership-list"),
        {"project": str(joined_project.pk)},
    )
    assert response.data["count"] == 1

    response = api_client.get(reverse("membership-list"), {"project": "not-a-uuid"})
    assert response.status_code == 400


@pytest.mark.django_db
def test_project_creator_can_add_member(api_client, user, other_user, owned_project):
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("membership-list"),
        {"project": str(owned_project.pk), "user": other_user.pk},
        format="json",
    )

    assert response.status_code == 201
    assert ProjectMembership.objects.filter(
        project=owned_project, user=other_user
    ).exists()


@pytest.mark.django_db
def test_project_member_cannot_add_member(
    api_client, user, member_user, joined_project
):
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("membership-list"),
        {"project": str(joined_project.pk), "user": member_user.pk},
        format="json",
    )

    assert response.status_code == 403
    assert not ProjectMembership.objects.filter(
        project=joined_project, user=member_user
    ).exists()


@pytest.mark.django_db
def test_administrator_can_add_member(api_client, admin_user, user, member_project):
    api_client.force_authenticate(user=admin_user)
    response = api_client.post(
        reverse("membership-list"),
        {"project": str(member_project.pk), "user": user.pk},
        format="json",
    )

    assert response.status_code == 201
    assert ProjectMembership.objects.filter(
        project=member_project, user=user
    ).exists()


@pytest.mark.django_db
def test_project_creator_cannot_be_added_as_member(api_client, user, owned_project):
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("membership-list"),
        {"project": str(owned_project.pk), "user": user.pk},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_inactive_user_cannot_be_added_as_member(api_client, user, owned_project):
    inactive_user = User.objects.create_user(
        username="inactive",
        email="inactive@example.com",
        password="test-password",
        is_active=False,
    )

    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("membership-list"),
        {"project": str(owned_project.pk), "user": inactive_user.pk},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_duplicate_membership_is_rejected(api_client, user, other_user, joined_project):
    api_client.force_authenticate(user=other_user)
    response = api_client.post(
        reverse("membership-list"),
        {"project": str(joined_project.pk), "user": user.pk},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_inaccessible_project_membership_returns_not_found(
    api_client, user, other_user, member_project
):
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("membership-list"),
        {"project": str(member_project.pk), "user": other_user.pk},
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_project_member_cannot_remove_membership(api_client, user, joined_project):
    membership = joined_project.memberships.get(user=user)

    api_client.force_authenticate(user=user)
    response = api_client.delete(
        reverse("membership-detail", args=[membership.pk])
    )

    assert response.status_code == 403
    assert ProjectMembership.objects.filter(pk=membership.pk).exists()


@pytest.mark.django_db
def test_project_creator_can_remove_membership(api_client, user, other_user, joined_project):
    membership = joined_project.memberships.get(user=user)

    api_client.force_authenticate(user=other_user)
    response = api_client.delete(
        reverse("membership-detail", args=[membership.pk])
    )

    assert response.status_code == 204
    assert not ProjectMembership.objects.filter(pk=membership.pk).exists()


@pytest.mark.django_db
def test_administrator_can_remove_membership(
    api_client, admin_user, member_user, member_project
):
    membership = member_project.memberships.get(user=member_user)

    api_client.force_authenticate(user=admin_user)
    response = api_client.delete(
        reverse("membership-detail", args=[membership.pk])
    )

    assert response.status_code == 204
    assert not ProjectMembership.objects.filter(pk=membership.pk).exists()


@pytest.mark.django_db
def test_archived_project_membership_remains_editable(
    api_client, user, other_user, owned_project
):
    owned_project.status = Project.Status.ARCHIVED
    owned_project.save(update_fields=["status"])

    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("membership-list"),
        {"project": str(owned_project.pk), "user": other_user.pk},
        format="json",
    )

    assert response.status_code == 201

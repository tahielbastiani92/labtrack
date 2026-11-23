import pytest
from django.urls import reverse

from apps.projects.models import Project
from apps.samples.models import Sample


@pytest.mark.django_db
def test_sample_list_is_scoped_to_visible_projects(
    api_client, user, sample, member_project, member_user
):
    hidden_sample = Sample.objects.create(
        project=member_project,
        code="S-999",
        sample_type="blood",
        created_by=member_user,
    )

    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("sample-list"))

    ids = {item["id"] for item in response.data["results"]}
    assert str(sample.pk) in ids
    assert str(hidden_sample.pk) not in ids


@pytest.mark.django_db
def test_sample_create_sets_creator_and_default_status(api_client, user, owned_project):
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("sample-list"),
        {
            "project": str(owned_project.pk),
            "code": " s-002 ",
            "sample_type": "serum",
            "collection_date": "2020-01-01",
            "notes": "Synthetic sample",
            "status": Sample.Status.CONSUMED,
        },
        format="json",
    )

    assert response.status_code == 201
    created = Sample.objects.get(pk=response.data["id"])
    assert created.code == "S-002"
    assert created.status == Sample.Status.REGISTERED
    assert created.created_by == user


@pytest.mark.django_db
def test_sample_create_rejects_inaccessible_project(
    api_client, user, member_project
):
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("sample-list"),
        {
            "project": str(member_project.pk),
            "code": "S-002",
            "sample_type": "serum",
        },
        format="json",
    )

    assert response.status_code == 400
    assert not Sample.objects.filter(code="S-002").exists()


@pytest.mark.django_db
def test_sample_create_is_blocked_in_archived_project(api_client, user, owned_project):
    owned_project.status = Project.Status.ARCHIVED
    owned_project.save(update_fields=["status"])

    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("sample-list"),
        {
            "project": str(owned_project.pk),
            "code": "S-002",
            "sample_type": "serum",
        },
        format="json",
    )

    assert response.status_code == 400
    assert not Sample.objects.filter(code="S-002").exists()


@pytest.mark.django_db
def test_sample_create_rejects_future_collection_date(api_client, user, owned_project):
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("sample-list"),
        {
            "project": str(owned_project.pk),
            "code": "S-002",
            "sample_type": "serum",
            "collection_date": "2999-01-01",
        },
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_sample_create_rejects_duplicate_code(api_client, user, owned_project, sample):
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("sample-list"),
        {
            "project": str(owned_project.pk),
            "code": " s-001 ",
            "sample_type": "serum",
        },
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_sample_update_rejects_invalid_status_transition(api_client, user, sample):
    api_client.force_authenticate(user=user)
    response = api_client.patch(
        reverse("sample-detail", args=[sample.pk]),
        {"status": Sample.Status.CONSUMED},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_sample_update_allows_valid_status_transition(api_client, user, sample):
    api_client.force_authenticate(user=user)
    response = api_client.patch(
        reverse("sample-detail", args=[sample.pk]),
        {"status": Sample.Status.PROCESSING},
        format="json",
    )

    assert response.status_code == 200
    sample.refresh_from_db()
    assert sample.status == Sample.Status.PROCESSING


@pytest.mark.django_db
def test_sample_project_cannot_be_changed(api_client, user, sample, joined_project):
    original_project_id = sample.project_id

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        reverse("sample-detail", args=[sample.pk]),
        {"project": str(joined_project.pk), "notes": "Updated"},
        format="json",
    )

    assert response.status_code == 200
    sample.refresh_from_db()
    assert sample.project_id == original_project_id
    assert sample.notes == "Updated"


@pytest.mark.django_db
def test_sample_update_and_delete_are_blocked_in_archived_project(
    api_client, user, sample
):
    sample.project.status = Project.Status.ARCHIVED
    sample.project.save(update_fields=["status"])

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        reverse("sample-detail", args=[sample.pk]),
        {"notes": "Updated"},
        format="json",
    )
    assert response.status_code == 403

    response = api_client.delete(reverse("sample-detail", args=[sample.pk]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_sample_list_filters(api_client, user, sample, owned_project):
    Sample.objects.create(
        project=owned_project,
        code="S-002",
        sample_type="serum",
        status=Sample.Status.STORED,
        created_by=user,
    )

    api_client.force_authenticate(user=user)

    response = api_client.get(reverse("sample-list"), {"q": "S-001"})
    assert response.data["count"] == 1

    response = api_client.get(reverse("sample-list"), {"type": "serum"})
    assert response.data["count"] == 1

    response = api_client.get(reverse("sample-list"), {"status": Sample.Status.STORED})
    assert response.data["count"] == 1

    response = api_client.get(
        reverse("sample-list"),
        {"project": str(owned_project.pk)},
    )
    assert response.data["count"] == 2

    response = api_client.get(reverse("sample-list"), {"project": "not-a-uuid"})
    assert response.status_code == 400

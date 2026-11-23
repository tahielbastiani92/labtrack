import pytest
from django.urls import reverse

from apps.datasets.models import Dataset
from apps.projects.models import Project
from apps.samples.models import Sample


@pytest.mark.django_db
def test_dataset_list_is_scoped_to_visible_projects(
    api_client, user, dataset, member_project, member_user
):
    hidden_dataset = Dataset.objects.create(
        project=member_project,
        name="Hidden dataset",
        created_by=member_user,
    )

    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("dataset-list"))

    ids = {item["id"] for item in response.data["results"]}
    assert str(dataset.pk) in ids
    assert str(hidden_dataset.pk) not in ids


@pytest.mark.django_db
def test_dataset_create_links_same_project_samples(api_client, user, owned_project, sample):
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("dataset-list"),
        {
            "project": str(owned_project.pk),
            "name": "API dataset",
            "description": "Synthetic dataset",
            "data_format": Dataset.DataFormat.CSV,
            "storage_uri": "s3://synthetic/example.csv",
            "samples": [str(sample.pk)],
        },
        format="json",
    )

    assert response.status_code == 201
    created = Dataset.objects.get(pk=response.data["id"])
    assert created.created_by == user
    assert list(created.samples.all()) == [sample]
    assert response.data["samples"] == [sample.pk]


@pytest.mark.django_db
def test_dataset_create_rejects_cross_project_samples(
    api_client, user, owned_project, joined_project
):
    foreign_sample = Sample.objects.create(
        project=joined_project,
        code="S-002",
        sample_type="serum",
        created_by=user,
    )

    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("dataset-list"),
        {
            "project": str(owned_project.pk),
            "name": "Invalid dataset",
            "samples": [str(foreign_sample.pk)],
        },
        format="json",
    )

    assert response.status_code == 400
    assert not Dataset.objects.filter(name="Invalid dataset").exists()


@pytest.mark.django_db
def test_dataset_create_rejects_inaccessible_project(
    api_client, user, member_project
):
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("dataset-list"),
        {
            "project": str(member_project.pk),
            "name": "Invalid dataset",
        },
        format="json",
    )

    assert response.status_code == 400
    assert not Dataset.objects.filter(name="Invalid dataset").exists()


@pytest.mark.django_db
def test_dataset_create_is_blocked_in_archived_project(api_client, user, owned_project):
    owned_project.status = Project.Status.ARCHIVED
    owned_project.save(update_fields=["status"])

    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("dataset-list"),
        {
            "project": str(owned_project.pk),
            "name": "Invalid dataset",
        },
        format="json",
    )

    assert response.status_code == 400
    assert not Dataset.objects.filter(name="Invalid dataset").exists()


@pytest.mark.django_db
def test_dataset_project_cannot_be_changed(api_client, user, dataset, joined_project):
    original_project_id = dataset.project_id

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        reverse("dataset-detail", args=[dataset.pk]),
        {"project": str(joined_project.pk), "name": "Renamed dataset"},
        format="json",
    )

    assert response.status_code == 200
    dataset.refresh_from_db()
    assert dataset.project_id == original_project_id
    assert dataset.name == "Renamed dataset"


@pytest.mark.django_db
def test_dataset_update_and_delete_are_blocked_in_archived_project(
    api_client, user, dataset
):
    dataset.project.status = Project.Status.ARCHIVED
    dataset.project.save(update_fields=["status"])

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        reverse("dataset-detail", args=[dataset.pk]),
        {"name": "Renamed dataset"},
        format="json",
    )
    assert response.status_code == 403

    response = api_client.delete(reverse("dataset-detail", args=[dataset.pk]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_dataset_list_filters(api_client, user, dataset, owned_project):
    Dataset.objects.create(
        project=owned_project,
        name="CSV dataset",
        data_format=Dataset.DataFormat.CSV,
        created_by=user,
    )

    api_client.force_authenticate(user=user)

    response = api_client.get(reverse("dataset-list"), {"q": "Dataset A"})
    assert response.data["count"] == 1

    response = api_client.get(
        reverse("dataset-list"),
        {"data_format": Dataset.DataFormat.CSV},
    )
    assert response.data["count"] == 1

    response = api_client.get(
        reverse("dataset-list"),
        {"project": str(owned_project.pk)},
    )
    assert response.data["count"] == 2

    response = api_client.get(reverse("dataset-list"), {"project": "not-a-uuid"})
    assert response.status_code == 400

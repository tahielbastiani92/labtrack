import pytest
from django.urls import reverse

from apps.datasets.models import Dataset
from apps.projects.models import Project
from apps.samples.models import Sample


@pytest.mark.django_db
def test_dataset_list_requires_login(client):
    response = client.get(reverse("datasets:list"))

    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_dataset_create_links_same_project_samples(client, user, owned_project, sample):
    client.force_login(user)
    response = client.post(
        reverse("datasets:create", args=[owned_project.pk]),
        {
            "name": "Combined reads",
            "description": "Synthetic dataset",
            "data_format": "CSV",
            "storage_uri": "s3://demo/combined.csv",
            "samples": [str(sample.pk)],
        },
    )

    assert response.status_code == 302
    dataset = Dataset.objects.get(name="Combined reads")
    assert dataset.project == owned_project
    assert dataset.created_by == user
    assert list(dataset.samples.all()) == [sample]


@pytest.mark.django_db
def test_dataset_create_rejects_cross_project_samples(
    client, user, owned_project, member_project, other_user
):
    foreign = Sample.objects.create(
        project=member_project,
        code="S-999",
        sample_type="blood",
        created_by=other_user,
    )
    client.force_login(user)
    response = client.post(
        reverse("datasets:create", args=[owned_project.pk]),
        {
            "name": "Cross project",
            "description": "",
            "data_format": "OTHER",
            "storage_uri": "",
            "samples": [str(foreign.pk)],
        },
    )

    assert response.status_code == 200
    assert "samples" in response.context["form"].errors
    assert not Dataset.objects.filter(name="Cross project").exists()


@pytest.mark.django_db
def test_dataset_create_is_blocked_in_archived_project(client, user, owned_project):
    owned_project.status = Project.Status.ARCHIVED
    owned_project.save(update_fields=["status"])

    client.force_login(user)
    response = client.post(
        reverse("datasets:create", args=[owned_project.pk]),
        {"name": "Blocked", "data_format": "OTHER"},
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_dataset_project_cannot_be_changed(client, user, dataset, member_project):
    original_project_id = dataset.project_id
    client.force_login(user)
    response = client.post(
        reverse("datasets:update", args=[dataset.pk]),
        {
            "project": member_project.pk,
            "name": dataset.name,
            "description": "",
            "data_format": dataset.data_format,
            "storage_uri": "",
        },
    )

    assert response.status_code == 302
    dataset.refresh_from_db()
    assert dataset.project_id == original_project_id


@pytest.mark.django_db
def test_dataset_detail_renders_for_visible_dataset(client, user, dataset, sample):
    dataset.samples.add(sample)
    client.force_login(user)
    response = client.get(reverse("datasets:detail", args=[dataset.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert dataset.name in content
    assert sample.code in content


@pytest.mark.django_db
def test_dataset_detail_is_hidden_from_non_members(client, user, member_project, other_user):
    hidden = Dataset.objects.create(
        project=member_project,
        name="Hidden dataset",
        created_by=other_user,
    )
    client.force_login(user)

    response = client.get(reverse("datasets:detail", args=[hidden.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_dataset_delete_does_not_delete_samples(client, user, dataset, sample):
    dataset.samples.add(sample)
    client.force_login(user)
    response = client.post(reverse("datasets:delete", args=[dataset.pk]))

    assert response.status_code == 302
    assert not Dataset.objects.filter(pk=dataset.pk).exists()
    assert Sample.objects.filter(pk=sample.pk).exists()


@pytest.mark.django_db
def test_dataset_list_is_scoped_and_filterable(client, user, dataset, member_project, other_user):
    dataset.data_format = Dataset.DataFormat.CSV
    dataset.save(update_fields=["data_format"])
    hidden = Dataset.objects.create(
        project=member_project,
        name="Hidden dataset",
        data_format=Dataset.DataFormat.CSV,
        created_by=other_user,
    )
    client.force_login(user)

    response = client.get(reverse("datasets:list"))
    content = response.content.decode()
    assert dataset.name in content
    assert hidden.name not in content

    response = client.get(reverse("datasets:list"), {"format": "FASTQ"})
    assert dataset.name not in response.content.decode()

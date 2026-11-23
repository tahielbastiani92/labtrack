import pytest

from apps.datasets.forms import DatasetAdminForm
from apps.projects.models import Project
from apps.samples.models import Sample


def _dataset_admin_data(dataset, samples):
    return {
        "project": dataset.project.pk,
        "name": dataset.name,
        "description": dataset.description,
        "data_format": dataset.data_format,
        "storage_uri": dataset.storage_uri,
        "samples": [sample.pk for sample in samples],
        "created_by": dataset.created_by.pk,
    }


@pytest.mark.django_db
def test_admin_form_rejects_cross_project_samples(dataset, other_user):
    other_project = Project.objects.create(name="Other project", created_by=other_user)
    foreign_sample = Sample.objects.create(
        project=other_project,
        code="S-999",
        sample_type="blood",
        created_by=other_user,
    )

    form = DatasetAdminForm(
        data=_dataset_admin_data(dataset, [foreign_sample]),
        instance=dataset,
    )

    assert not form.is_valid()
    assert "samples" in form.errors


@pytest.mark.django_db
def test_admin_form_rejects_writes_to_archived_project(dataset):
    dataset.project.status = Project.Status.ARCHIVED
    dataset.project.save(update_fields=["status"])

    form = DatasetAdminForm(
        data=_dataset_admin_data(dataset, []),
        instance=dataset,
    )

    assert not form.is_valid()
    assert "__all__" in form.errors

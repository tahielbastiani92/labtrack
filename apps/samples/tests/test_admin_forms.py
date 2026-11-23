import pytest

from apps.projects.models import Project
from apps.samples.forms import SampleAdminForm
from apps.samples.models import Sample


def _sample_admin_data(sample, status):
    return {
        "project": sample.project.pk,
        "code": sample.code,
        "sample_type": sample.sample_type,
        "collection_date": sample.collection_date,
        "status": status,
        "notes": sample.notes,
        "created_by": sample.created_by.pk,
    }


@pytest.mark.django_db
def test_admin_form_rejects_invalid_status_transition(sample):
    form = SampleAdminForm(
        data=_sample_admin_data(sample, Sample.Status.CONSUMED),
        instance=sample,
    )

    assert not form.is_valid()
    assert "status" in form.errors


@pytest.mark.django_db
def test_admin_form_rejects_writes_to_archived_project(sample):
    sample.project.status = Project.Status.ARCHIVED
    sample.project.save(update_fields=["status"])

    form = SampleAdminForm(
        data=_sample_admin_data(sample, sample.status),
        instance=sample,
    )

    assert not form.is_valid()
    assert "__all__" in form.errors

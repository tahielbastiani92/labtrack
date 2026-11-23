import pytest
from django.db import transaction
from django.db.models import ProtectedError

from apps.accounts.models import User
from apps.datasets.models import Dataset
from apps.projects.models import Project
from apps.samples.models import Sample


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        username="owner",
        email="owner@example.com",
        password="test-password",
    )


@pytest.fixture
def project(owner):
    return Project.objects.create(name="Project A", created_by=owner)


@pytest.mark.django_db
def test_dataset_can_be_linked_to_multiple_samples(project, owner):
    first = Sample.objects.create(
        project=project, code="S-001", sample_type="blood", created_by=owner
    )
    second = Sample.objects.create(
        project=project, code="S-002", sample_type="blood", created_by=owner
    )
    dataset = Dataset.objects.create(project=project, name="Combined reads", created_by=owner)

    dataset.samples.add(first, second)

    assert dataset.samples.count() == 2


@pytest.mark.django_db
def test_project_with_datasets_cannot_be_deleted(project, owner):
    Dataset.objects.create(project=project, name="Reads", created_by=owner)

    with pytest.raises(ProtectedError), transaction.atomic():
        project.delete()

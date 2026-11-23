import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.accounts.models import User
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
def test_sample_code_is_normalized(project, owner):
    sample = Sample.objects.create(
        project=project, code="  s-001  ", sample_type="blood", created_by=owner
    )

    assert sample.code == "S-001"


@pytest.mark.django_db
def test_sample_code_is_unique_within_project(project, owner):
    Sample.objects.create(project=project, code="S-001", sample_type="blood", created_by=owner)

    with pytest.raises(IntegrityError), transaction.atomic():
        Sample.objects.create(project=project, code="S-001", sample_type="serum", created_by=owner)


@pytest.mark.django_db
def test_same_code_allowed_in_different_projects(project, owner):
    other = Project.objects.create(name="Project B", created_by=owner)

    Sample.objects.create(project=project, code="S-001", sample_type="blood", created_by=owner)
    Sample.objects.create(project=other, code="S-001", sample_type="blood", created_by=owner)

    assert Sample.objects.filter(code="S-001").count() == 2


@pytest.mark.django_db
def test_project_with_samples_cannot_be_deleted(project, owner):
    Sample.objects.create(project=project, code="S-001", sample_type="blood", created_by=owner)

    with pytest.raises(ProtectedError), transaction.atomic():
        project.delete()

import pytest
from django.core.exceptions import ValidationError

from apps.datasets.rules import validate_samples_belong_to_project
from apps.samples.models import Sample


@pytest.mark.django_db
def test_same_project_samples_are_allowed(owned_project, sample):
    validate_samples_belong_to_project(owned_project, [sample])


@pytest.mark.django_db
def test_cross_project_samples_are_rejected(owned_project, member_project, other_user):
    foreign = Sample.objects.create(
        project=member_project,
        code="S-999",
        sample_type="blood",
        created_by=other_user,
    )

    with pytest.raises(ValidationError):
        validate_samples_belong_to_project(owned_project, [foreign])

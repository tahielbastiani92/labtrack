import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import User
from apps.datasets.models import Dataset
from apps.projects.models import Project, ProjectMembership
from apps.samples.models import Sample


@pytest.fixture
def demo_password(monkeypatch):
    monkeypatch.setenv("DEMO_USERS_PASSWORD", "test-demo-password")


@pytest.mark.django_db
def test_load_demo_data_creates_expected_records(demo_password):
    call_command("load_demo_data")

    assert User.objects.count() == 4
    assert Project.objects.count() == 3
    assert ProjectMembership.objects.count() == 5
    assert Sample.objects.count() == 18
    assert Dataset.objects.count() == 5

    admin = User.objects.get(username="demo_admin")
    assert admin.role == User.Role.ADMINISTRATOR
    assert admin.check_password("test-demo-password")


@pytest.mark.django_db
def test_load_demo_data_is_idempotent(demo_password):
    call_command("load_demo_data")
    call_command("load_demo_data")

    assert User.objects.count() == 4
    assert Project.objects.count() == 3
    assert ProjectMembership.objects.count() == 5
    assert Sample.objects.count() == 18
    assert Dataset.objects.count() == 5


@pytest.mark.django_db
def test_load_demo_data_does_not_overwrite_existing_records(demo_password):
    user = User.objects.create_user(
        username="demo_admin",
        email="demo_admin@example.com",
        password="original-password",
        first_name="Existing",
        role=User.Role.RESEARCHER,
    )

    call_command("load_demo_data")

    user.refresh_from_db()

    assert user.first_name == "Existing"
    assert user.role == User.Role.RESEARCHER
    assert user.check_password("original-password")


@pytest.mark.django_db
def test_load_demo_data_requires_password(monkeypatch):
    monkeypatch.delenv("DEMO_USERS_PASSWORD", raising=False)

    with pytest.raises(CommandError, match="DEMO_USERS_PASSWORD"):
        call_command("load_demo_data")

    assert User.objects.count() == 0
    assert Project.objects.count() == 0


@pytest.mark.django_db
def test_load_demo_data_creates_datasets_with_project_samples(demo_password):
    call_command("load_demo_data")

    for dataset in Dataset.objects.prefetch_related("samples"):
        assert dataset.samples.exists()

        for sample in dataset.samples.all():
            assert sample.project_id == dataset.project_id


@pytest.mark.django_db
def test_load_demo_data_does_not_add_members_to_existing_projects(
    demo_password,
):
    creator = User.objects.create_user(
        username="researcher_anna",
        email="anna@example.com",
        password="original-password",
    )
    existing_member = User.objects.create_user(
        username="existing_member",
        email="existing@example.com",
        password="original-password",
    )
    project = Project.objects.create(
        name="Fermentation Monitoring",
        description="Existing project",
        status=Project.Status.ACTIVE,
        created_by=creator,
    )
    ProjectMembership.objects.create(
        project=project,
        user=existing_member,
    )

    call_command("load_demo_data")

    project.refresh_from_db()

    assert project.description == "Existing project"
    assert project.members.count() == 1
    assert project.members.filter(pk=existing_member.pk).exists()
import pytest

from apps.accounts.models import User
from apps.projects.models import Project, ProjectMembership
from apps.samples.models import Sample
from apps.datasets.models import Dataset


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="researcher",
        email="researcher@example.com",
        password="test-password",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="other",
        email="other@example.com",
        password="test-password",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin",
        email="admin@example.com",
        password="test-password",
        role=User.Role.ADMINISTRATOR,
    )


@pytest.fixture
def member_user(db):
    return User.objects.create_user(
        username="member",
        email="member@example.com",
        password="test-password",
    )


@pytest.fixture
def owned_project(user):
    return Project.objects.create(name="Owned project", created_by=user)


@pytest.fixture
def joined_project(other_user, user):
    project = Project.objects.create(name="Joined project", created_by=other_user)
    ProjectMembership.objects.create(project=project, user=user)
    return project


@pytest.fixture
def member_project(other_user, member_user):
    project = Project.objects.create(name="Member project", created_by=other_user)
    ProjectMembership.objects.create(project=project, user=member_user)
    return project


@pytest.fixture
def sample(owned_project, user):
    return Sample.objects.create(
        project=owned_project,
        code="S-001",
        sample_type="blood",
        created_by=user,
    )


@pytest.fixture
def dataset(owned_project, user):
    return Dataset.objects.create(
        project=owned_project,
        name="Dataset A",
        created_by=user,
    )

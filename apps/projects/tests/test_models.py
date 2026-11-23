import pytest
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.projects.models import Project, ProjectMembership


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        username="owner",
        email="owner@example.com",
        password="test-password",
    )


@pytest.fixture
def member(db):
    return User.objects.create_user(
        username="member",
        email="member@example.com",
        password="test-password",
    )


@pytest.mark.django_db
def test_project_membership_is_unique_per_project_and_user(owner, member):
    project = Project.objects.create(name="Project A", created_by=owner)
    ProjectMembership.objects.create(project=project, user=member)

    with pytest.raises(IntegrityError), transaction.atomic():
        ProjectMembership.objects.create(project=project, user=member)


@pytest.mark.django_db
def test_same_user_can_join_multiple_projects(owner, member):
    first = Project.objects.create(name="Project A", created_by=owner)
    second = Project.objects.create(name="Project B", created_by=owner)

    ProjectMembership.objects.create(project=first, user=member)
    ProjectMembership.objects.create(project=second, user=member)

    assert member.project_memberships.count() == 2

import pytest
from django.contrib.auth.models import AnonymousUser

from apps.projects.access import can_manage_project, project_is_writable, projects_visible_to
from apps.projects.models import Project


@pytest.mark.django_db
def test_anonymous_user_sees_no_projects(owned_project):
    assert not projects_visible_to(AnonymousUser()).exists()


@pytest.mark.django_db
def test_researcher_sees_owned_and_joined_projects(
    user, owned_project, joined_project, member_project
):
    visible = set(projects_visible_to(user).values_list("pk", flat=True))

    assert owned_project.pk in visible
    assert joined_project.pk in visible
    assert member_project.pk not in visible


@pytest.mark.django_db
def test_administrator_sees_all_projects(admin_user, owned_project, joined_project, member_project):
    visible = set(projects_visible_to(admin_user).values_list("pk", flat=True))

    assert visible == {owned_project.pk, joined_project.pk, member_project.pk}


@pytest.mark.django_db
def test_only_creator_or_administrator_can_manage_project(
    user, member_user, admin_user, owned_project, member_project
):
    assert can_manage_project(user, owned_project)
    assert can_manage_project(admin_user, member_project)
    assert not can_manage_project(member_user, member_project)


@pytest.mark.django_db
def test_archived_project_is_not_writable(owned_project):
    owned_project.status = Project.Status.ARCHIVED

    assert not project_is_writable(owned_project)

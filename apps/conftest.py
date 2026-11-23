import pytest

from apps.accounts.models import User


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

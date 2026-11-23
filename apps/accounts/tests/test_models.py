import pytest
from django.db import IntegrityError, transaction

from apps.accounts.models import User


@pytest.mark.django_db
def test_new_user_defaults_to_researcher():
    user = User.objects.create_user(
        username="researcher",
        email="researcher@example.com",
        password="test-password",
    )

    assert user.role == User.Role.RESEARCHER
    assert user.is_administrator is False


@pytest.mark.django_db
def test_administrator_role_is_exposed_by_helper():
    user = User.objects.create_user(
        username="admin",
        email="admin@example.com",
        password="test-password",
        role=User.Role.ADMINISTRATOR,
    )

    assert user.is_administrator is True


@pytest.mark.django_db
def test_email_is_normalized_to_lowercase():
    user = User.objects.create_user(
        username="normalized",
        email="  Mixed.Case@Example.COM  ",
        password="test-password",
    )

    assert user.email == "mixed.case@example.com"


@pytest.mark.django_db
def test_email_uniqueness_is_case_insensitive_after_normalization():
    User.objects.create_user(
        username="first",
        email="Case@Example.com",
        password="test-password",
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(
            username="second",
            email="case@example.com",
            password="test-password",
        )


@pytest.mark.django_db
def test_email_is_unique():
    User.objects.create_user(
        username="first",
        email="shared@example.com",
        password="test-password",
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(
            username="second",
            email="shared@example.com",
            password="test-password",
        )

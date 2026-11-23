import pytest
from django.urls import reverse

from apps.accounts.models import User

PASSWORD = "S3cure-Passphrase-2026"


def _create_data(**overrides):
    data = {
        "username": "newuser",
        "first_name": "New",
        "last_name": "User",
        "email": "NEW@Example.com",
        "role": User.Role.RESEARCHER,
        "is_active": "on",
        "password1": PASSWORD,
        "password2": PASSWORD,
    }
    data.update(overrides)
    return data


def _update_data(user, **overrides):
    data = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role,
        "is_active": "on" if user.is_active else "",
        "new_password1": "",
        "new_password2": "",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_user_management_requires_login(client):
    response = client.get(reverse("accounts:user_list"))

    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_user_management_rejects_researchers(client, user):
    client.force_login(user)
    response = client.get(reverse("accounts:user_list"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_administrator_can_list_users(client, admin_user, user):
    client.force_login(admin_user)
    response = client.get(reverse("accounts:user_list"))

    assert response.status_code == 200
    content = response.content.decode()
    assert user.username in content
    assert admin_user.username in content
    assert "New user" in content


@pytest.mark.django_db
def test_administrator_can_create_user(client, admin_user):
    client.force_login(admin_user)
    response = client.post(reverse("accounts:user_create"), _create_data())

    assert response.status_code == 302
    created = User.objects.get(username="newuser")
    assert created.email == "new@example.com"
    assert created.role == User.Role.RESEARCHER
    assert created.is_active is True
    assert created.check_password(PASSWORD)


@pytest.mark.django_db
def test_administrator_can_create_another_administrator(client, admin_user):
    client.force_login(admin_user)
    response = client.post(
        reverse("accounts:user_create"),
        _create_data(role=User.Role.ADMINISTRATOR),
    )

    assert response.status_code == 302
    assert User.objects.get(username="newuser").role == User.Role.ADMINISTRATOR


@pytest.mark.django_db
def test_create_user_rejects_password_mismatch(client, admin_user):
    client.force_login(admin_user)
    response = client.post(
        reverse("accounts:user_create"),
        _create_data(password2="different-password"),
    )

    assert response.status_code == 200
    assert not User.objects.filter(username="newuser").exists()
    assert "did not match" in response.content.decode()


@pytest.mark.django_db
def test_create_user_applies_password_validators(client, admin_user):
    client.force_login(admin_user)
    response = client.post(
        reverse("accounts:user_create"),
        _create_data(password1="12345678", password2="12345678"),
    )

    assert response.status_code == 200
    assert not User.objects.filter(username="newuser").exists()


@pytest.mark.django_db
def test_create_user_rejects_duplicate_email_case_insensitively(
    client, admin_user, other_user
):
    client.force_login(admin_user)
    response = client.post(
        reverse("accounts:user_create"),
        _create_data(email=other_user.email.upper()),
    )

    assert response.status_code == 200
    assert not User.objects.filter(username="newuser").exists()
    assert "already exists" in response.content.decode().lower()


@pytest.mark.django_db
def test_administrator_can_change_role_and_deactivate_user(
    client, admin_user, other_user
):
    client.force_login(admin_user)
    response = client.post(
        reverse("accounts:user_update", args=[other_user.pk]),
        _update_data(other_user, role=User.Role.ADMINISTRATOR),
    )
    assert response.status_code == 302
    other_user.refresh_from_db()
    assert other_user.role == User.Role.ADMINISTRATOR

    response = client.post(
        reverse("accounts:user_update", args=[other_user.pk]),
        _update_data(other_user, is_active=""),
    )
    assert response.status_code == 302
    other_user.refresh_from_db()
    assert other_user.is_active is False


@pytest.mark.django_db
def test_administrator_can_reset_user_password(client, admin_user, other_user):
    client.force_login(admin_user)
    response = client.post(
        reverse("accounts:user_update", args=[other_user.pk]),
        _update_data(
            other_user,
            new_password1="N3w-Passphrase-2026",
            new_password2="N3w-Passphrase-2026",
        ),
    )

    assert response.status_code == 302
    other_user.refresh_from_db()
    assert other_user.check_password("N3w-Passphrase-2026")


@pytest.mark.django_db
def test_blank_password_keeps_current_password(client, admin_user, other_user):
    client.force_login(admin_user)
    response = client.post(
        reverse("accounts:user_update", args=[other_user.pk]),
        _update_data(other_user),
    )

    assert response.status_code == 302
    other_user.refresh_from_db()
    assert other_user.check_password("test-password")


@pytest.mark.django_db
def test_administrator_cannot_deactivate_own_account(client, admin_user):
    client.force_login(admin_user)
    response = client.post(
        reverse("accounts:user_update", args=[admin_user.pk]),
        _update_data(admin_user, is_active=""),
    )

    assert response.status_code == 200
    admin_user.refresh_from_db()
    assert admin_user.is_active is True
    assert "cannot deactivate your own account" in response.content.decode()


@pytest.mark.django_db
def test_administrator_cannot_remove_own_administrator_role(client, admin_user):
    client.force_login(admin_user)
    response = client.post(
        reverse("accounts:user_update", args=[admin_user.pk]),
        _update_data(admin_user, role=User.Role.RESEARCHER),
    )

    assert response.status_code == 200
    admin_user.refresh_from_db()
    assert admin_user.role == User.Role.ADMINISTRATOR
    assert "cannot remove your own administrator role" in response.content.decode()


@pytest.mark.django_db
def test_user_list_filters(client, admin_user, user, other_user):
    other_user.is_active = False
    other_user.save(update_fields=["is_active"])
    client.force_login(admin_user)

    response = client.get(reverse("accounts:user_list"), {"q": "other"})
    content = response.content.decode()
    assert f">{other_user.username}</td>" in content
    assert f">{user.username}</td>" not in content

    response = client.get(reverse("accounts:user_list"), {"role": User.Role.ADMINISTRATOR})
    content = response.content.decode()
    assert f">{admin_user.username}</td>" in content
    assert f">{user.username}</td>" not in content

    response = client.get(reverse("accounts:user_list"), {"active": "0"})
    content = response.content.decode()
    assert f">{other_user.username}</td>" in content
    assert f">{user.username}</td>" not in content


@pytest.mark.django_db
def test_users_navbar_link_is_administrator_only(client, admin_user, user):
    client.force_login(admin_user)
    response = client.get(reverse("dashboard"))
    assert reverse("accounts:user_list") in response.content.decode()

    client.force_login(user)
    response = client.get(reverse("dashboard"))
    assert reverse("accounts:user_list") not in response.content.decode()

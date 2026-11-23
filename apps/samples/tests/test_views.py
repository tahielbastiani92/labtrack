import pytest
from django.urls import reverse

from apps.projects.models import Project
from apps.samples.models import Sample


@pytest.mark.django_db
def test_sample_list_requires_login(client):
    response = client.get(reverse("samples:list"))

    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_sample_create_sets_project_creator_and_default_status(client, user, owned_project):
    client.force_login(user)
    response = client.post(
        reverse("samples:create", args=[owned_project.pk]),
        {
            "code": "  s-002  ",
            "sample_type": "serum",
            "collection_date": "2020-01-01",
            "notes": "Synthetic note",
        },
    )

    assert response.status_code == 302
    sample = Sample.objects.get(code="S-002")
    assert sample.project == owned_project
    assert sample.created_by == user
    assert sample.status == Sample.Status.REGISTERED


@pytest.mark.django_db
def test_sample_create_is_hidden_for_inaccessible_project(client, user, member_project):
    client.force_login(user)
    response = client.post(
        reverse("samples:create", args=[member_project.pk]),
        {"code": "S-404", "sample_type": "blood"},
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_sample_create_is_blocked_in_archived_project(client, user, owned_project):
    owned_project.status = Project.Status.ARCHIVED
    owned_project.save(update_fields=["status"])

    client.force_login(user)
    response = client.post(
        reverse("samples:create", args=[owned_project.pk]),
        {"code": "S-002", "sample_type": "blood"},
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_sample_update_allows_valid_transition(client, user, sample):
    client.force_login(user)
    response = client.post(
        reverse("samples:update", args=[sample.pk]),
        {
            "code": sample.code,
            "sample_type": sample.sample_type,
            "collection_date": "",
            "status": "stored",
            "notes": "",
        },
    )

    assert response.status_code == 302
    sample.refresh_from_db()
    assert sample.status == Sample.Status.STORED


@pytest.mark.django_db
def test_sample_update_rejects_invalid_transition(client, user, sample):
    client.force_login(user)
    response = client.post(
        reverse("samples:update", args=[sample.pk]),
        {
            "code": sample.code,
            "sample_type": sample.sample_type,
            "collection_date": "",
            "status": "consumed",
            "notes": "",
        },
    )

    assert response.status_code == 200
    assert "status" in response.context["form"].errors
    sample.refresh_from_db()
    assert sample.status == Sample.Status.REGISTERED


@pytest.mark.django_db
def test_sample_update_rejects_future_collection_date(client, user, sample):
    client.force_login(user)
    response = client.post(
        reverse("samples:update", args=[sample.pk]),
        {
            "code": sample.code,
            "sample_type": sample.sample_type,
            "collection_date": "2999-01-01",
            "status": sample.status,
            "notes": "",
        },
    )

    assert response.status_code == 200
    assert "collection_date" in response.context["form"].errors


@pytest.mark.django_db
def test_sample_project_cannot_be_changed(client, user, sample, member_project):
    original_project_id = sample.project_id
    client.force_login(user)
    response = client.post(
        reverse("samples:update", args=[sample.pk]),
        {
            "project": member_project.pk,
            "code": sample.code,
            "sample_type": sample.sample_type,
            "collection_date": "",
            "status": sample.status,
            "notes": "",
        },
    )

    assert response.status_code == 302
    sample.refresh_from_db()
    assert sample.project_id == original_project_id


@pytest.mark.django_db
def test_sample_detail_renders_for_visible_sample(client, user, sample, dataset):
    dataset.samples.add(sample)
    client.force_login(user)
    response = client.get(reverse("samples:detail", args=[sample.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert sample.code in content
    assert dataset.name in content


@pytest.mark.django_db
def test_sample_detail_is_hidden_from_non_members(client, user, member_project, other_user):
    hidden = Sample.objects.create(
        project=member_project,
        code="S-999",
        sample_type="blood",
        created_by=other_user,
    )
    client.force_login(user)

    response = client.get(reverse("samples:detail", args=[hidden.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_sample_delete_is_blocked_in_archived_project(client, user, owned_project, sample):
    owned_project.status = Project.Status.ARCHIVED
    owned_project.save(update_fields=["status"])

    client.force_login(user)
    response = client.post(reverse("samples:delete", args=[sample.pk]))

    assert response.status_code == 403
    assert Sample.objects.filter(pk=sample.pk).exists()


@pytest.mark.django_db
def test_sample_list_is_scoped_and_filterable(client, user, sample, member_project, other_user):
    hidden = Sample.objects.create(
        project=member_project,
        code="S-999",
        sample_type="serum",
        created_by=other_user,
    )
    client.force_login(user)

    response = client.get(reverse("samples:list"))
    assert sample.code in response.content.decode()
    assert hidden.code not in response.content.decode()

    response = client.get(reverse("samples:list"), {"status": "stored"})
    assert sample.code not in response.content.decode()

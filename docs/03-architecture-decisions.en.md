# Architecture Decisions — LabTrack

**Status:** Initial decisions
**Date:** 22 November 2026 (updated 23 November 2026)

## ADR-001 — Django-rendered UI plus REST API

**Decision:** Build the MVP with Django templates and Bootstrap for the browser interface, and Django REST Framework for API access.

**Rationale:** This keeps the project focused on the user's strongest relevant experience (Python/Django) while still demonstrating API design. A separate React application would increase scope and is not required to demonstrate the core requirements.

**Consequence:** Keep domain logic independent of templates so the API and HTML interface can share validation and authorization rules.

## ADR-002 — Custom user model from the first migration

**Decision:** Create `accounts.User` by extending `AbstractUser` and set `AUTH_USER_MODEL` before the first migration.

**Rationale:** The product needs an application role. Changing user models after the project has accumulated migrations and data is significantly more difficult.

**Consequence:** The custom user model must be created before the first `migrate` operation. Do not postpone it.

## ADR-003 — Project-scoped access

**Decision:** Researchers can access projects they created or joined. Administrators can access all projects.

**Rationale:** Project membership provides a clear boundary for protecting samples and datasets.

**Consequence:** Every HTML and API queryset must be scoped to the authenticated user's authorized projects. Object-level checks alone are not sufficient for list endpoints.

## ADR-004 — Dataset-to-sample many-to-many relationship

**Decision:** A dataset belongs to one project and may be associated with multiple samples from that same project.

**Rationale:** Some datasets may combine or derive from multiple samples.

**Consequence:** Enforce same-project consistency in a shared validation/service boundary and cover all write paths with tests.

## ADR-005 — Metadata-only dataset registration

**Decision:** Store a dataset's external location as metadata (`storage_uri`); do not upload or fetch files in the MVP.

**Rationale:** File storage, access control, size limits, malware scanning, and scientific file formats would materially expand the scope.

**Consequence:** Treat the value as untrusted text. Do not automatically dereference it or make outbound requests to it.

## ADR-006 — Toolchain versions

**Decision:** Target Python 3.13, Django 6.1.x, Django REST Framework 3.18.x, and PostgreSQL 17.

**Rationale:** Official Django documentation lists Python 3.13 as supported by Django 6.1; DRF's current requirements list Django 6.1 and Python 3.13 as supported. The selected PostgreSQL major is a stable supported release for this project.

**Consequence:** Use compatible current patch releases and verify dependency resolution with `uv lock`/`uv sync`. Re-check official compatibility before changing framework minor versions.

## ADR-007 — Session and token authentication for the API

**Decision:** Support session authentication for the browsable API and token authentication (`rest_framework.authtoken`) for independent API clients.

**Rationale:** The product requires an API usable outside the Django-rendered interface. Token authentication provides this without adding a third-party JWT dependency.

**Consequence:** All API endpoints require authentication. Tokens are provisioned through the shell or a future API endpoint in the MVP. The API must not expose unrestricted querysets under either authentication scheme.

## ADR-008 — Archived projects are read-only

**Decision:** A project with status `archived` rejects creation, update, and deletion of its samples and datasets. `completed` projects remain writable.

**Rationale:** Archiving communicates that a project's records should no longer change, while keeping the MVP simple and avoiding a separate soft-delete mechanism.

**Consequence:** The rule must be enforced in the shared write path used by HTML forms, API serializers, and admin actions. Project metadata and membership remain editable by the creator or an administrator.

## ADR-009 — Explicit sample status lifecycle

**Decision:** Sample status changes follow a fixed transition map; `consumed` and `discarded` are terminal.

**Rationale:** A lifecycle prevents accidental reopening of finished or discarded samples and gives the portfolio project a meaningful, testable business rule.

**Consequence:** Status validation belongs in the shared write path, not only in templates. Tests must cover every allowed transition and representative rejected transitions.

## ADR-010 — Application-level user administration

**Decision:** Administrators create, edit, deactivate, and reset passwords for application users through Django-rendered views. The application UI does not hard-delete users.

**Rationale:** Routine user administration should not require Django admin. Deactivation preserves `created_by` references and the records a user created, while keeping account management available to application administrators.

**Consequence:** Only users with the `administrator` application role can access these views; authorization is enforced server-side. Administrators cannot deactivate their own account or remove their own administrator role. Password handling uses Django's password validators and `set_password()`.

## ADR-011 — Flat, project-scoped API resources

**Decision:** Expose projects, memberships, samples, and datasets as flat `ModelViewSet` resources under `/api/v1/`. Querysets are scoped to projects the authenticated user can access. `project` is required when creating samples or datasets and is immutable on update. `created_by` is read-only. A token endpoint is provided at `/api/v1/auth/token/`.

**Rationale:** Flat resources keep the API usable independently without nested-route complexity. The same access and validation rules apply to HTML views and API serializers.

**Consequence:** Inaccessible detail records return 404. Any authenticated user may create projects; only the creator or an administrator may update or delete a project. Project memberships are visible to users with project access, while create and delete operations are restricted to the creator or an administrator. Archived projects reject sample and dataset writes. Dataset/sample associations must stay within the dataset's project. List filters are explicit, and dataset format filtering uses `data_format` because `format` is reserved by Django REST Framework.

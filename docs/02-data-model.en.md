# Initial Data Model — LabTrack

**Document status:** Proposed initial model
**Version:** 1.0
**Date:** 22 November 2026

## 1. Modeling principles

- Use UUID primary keys for domain records exposed through URLs or APIs.
- Use Django's custom user model from the first migration.
- Keep project ownership and project membership explicit.
- A sample belongs to one project only.
- A dataset belongs to one project and can reference multiple samples from that same project.
- Enforce same-project dataset/sample associations in application validation and test them thoroughly.
- Use database uniqueness constraints for rules that can be expressed at the database level.

## 2. Entities

### 2.1 User (`accounts.User`)
Extends `django.contrib.auth.models.AbstractUser`.

| Field | Type | Rules |
|---|---|---|
| id | Django user primary key | Keep Django's standard user PK for auth compatibility |
| username | inherited | Unique according to Django configuration |
| email | inherited | Required; unique; normalized to lowercase |
| role | choices | `administrator`, `researcher`; default `researcher` |
| is_active | inherited | Django account activation |
| date_joined | inherited | Django timestamp |

`is_staff` and `is_superuser` remain Django technical permissions. The application role is a separate business-level role. Do not automatically grant superuser privileges to every `administrator` role.

Application administrators manage user accounts through the web interface. Accounts are deactivated rather than deleted when they have created records; hard deletion is not exposed in the application UI.

### 2.2 Project (`projects.Project`)

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| name | CharField | Required; bounded length |
| description | TextField | Optional |
| status | choices | `active`, `completed`, `archived`; default `active` |
| created_by | FK → User | Required; `PROTECT`; immutable after creation |
| members | M2M → User through ProjectMembership | Additional researchers |
| created_at | DateTimeField | Set on creation |
| updated_at | DateTimeField | Updated on save |

Project names need not be globally unique.

### 2.3 ProjectMembership (`projects.ProjectMembership`)

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| project | FK → Project | Required; `CASCADE` when the project is deleted |
| user | FK → User | Required; `CASCADE`; must be an active user and must not be the project creator |
| joined_at | DateTimeField | Set on creation |

Constraint: unique `(project, user)`.

The creator already has access through `created_by`; membership rows are for additional users. Do not create a membership row for the creator, and reject attempts to add the creator as a member. Removing a user from the membership table removes project access but does not delete records they created.

### 2.4 Sample (`samples.Sample`)

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| project | FK → Project | Required; `PROTECT` |
| code | CharField | Required; trimmed and uppercased; unique within project |
| sample_type | CharField | Required; free text in the MVP |
| collection_date | DateField | Optional; must not be in the future |
| status | choices | `registered`, `processing`, `stored`, `consumed`, `discarded`; default `registered` |
| notes | TextField | Optional; no sensitive personal data |
| created_by | FK → User | Required; `PROTECT`; set from the authenticated user |
| created_at | DateTimeField | Set on creation |
| updated_at | DateTimeField | Updated on save |

Constraint: unique `(project, code)`.

The project relationship is immutable after creation in the MVP. Enforce this in the update path and test it. A database trigger is not required for this portfolio MVP.

Allowed status transitions:
- `registered` → `processing`, `stored`, `discarded`
- `processing` → `stored`, `consumed`, `discarded`
- `stored` → `processing`, `consumed`, `discarded`
- `consumed` and `discarded` are terminal.

Enforce transitions in the shared write path used by HTML forms and API serializers. Setting the current status is a no-op.

### 2.5 Dataset (`datasets.Dataset`)

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| project | FK → Project | Required; `PROTECT`; immutable after creation |
| name | CharField | Required; duplicates allowed within a project |
| description | TextField | Optional |
| data_format | choices | `FASTQ`, `FASTA`, `CSV`, `OTHER`; default `OTHER` |
| storage_uri | CharField | Optional; max length 2048; external location metadata only; never fetched or rendered as a link |
| samples | M2M → Sample | Optional; all samples must belong to the same project |
| created_by | FK → User | Required; `PROTECT`; set from the authenticated user |
| created_at | DateTimeField | Set on creation |
| updated_at | DateTimeField | Updated on save |

A dataset is project-scoped even when it has no sample associations. A dataset may be linked to multiple samples, but every linked sample must have the same `project_id` as the dataset. The dataset's project is immutable after creation; changing it would invalidate existing associations.

The cross-project rule cannot be guaranteed by a simple ordinary foreign key across this many-to-many relation. Validate it in a single well-defined domain/service or serializer boundary and test every write path. Do not rely only on form validation.

## 3. Relationships and cardinalities

```text
User 1 ──────── * Project                 (created_by)
User * ──────── * Project                 (through ProjectMembership)
Project 1 ───── * Sample
Project 1 ───── * Dataset
Dataset * ───── * Sample                  (same project required)
User 1 ──────── * Sample                  (created_by)
User 1 ──────── * Dataset                 (created_by)
```

## 4. Authorization rules

- Administrator application role: may access all projects and their related records.
- Researcher: may access a project if `created_by == request.user` or a membership row exists.
- Inactive users cannot authenticate and therefore cannot access project data.
- Project-scoped querysets must be filtered before retrieving detail records.
- A detail endpoint must not disclose whether an inaccessible record exists; use the project's standard not-found behavior for out-of-scope records.
- Only the creator or an administrator may change project metadata, status, or membership in the MVP.
- Any researcher with project access may manage samples and datasets within that project in the MVP, except when the project is `archived`.
- `archived` projects are read-only for samples and datasets. `completed` projects remain writable.
- Apply the same rules to HTML views, API views, related-object selectors, and Django admin.
- The API accepts session authentication for the browsable interface and token authentication for independent clients.

## 5. Deletion policy

Concrete choices:
- `created_by` references use `PROTECT` so deleting a user does not cascade-delete research records. Deactivate users instead of deleting them when they have created records.
- `ProjectMembership.project` and `ProjectMembership.user` use `CASCADE`; removing a project or a user removes the membership rows.
- Deleting a project is allowed only when it has no samples or datasets, and only the creator or an administrator may do it. The `PROTECT` foreign keys on samples and datasets enforce this at the database level.
- Deleting a sample removes its many-to-many associations from datasets, but does not delete datasets.
- Deleting a dataset does not delete samples.
- Sample and dataset deletion is blocked while the project is `archived`.
- The UI must use explicit confirmation for destructive actions.
- Add tests for each deletion rule.

## 6. Indexes and constraints

At minimum:
- Unique constraint `(project, code)` on Sample.
- Unique constraint `(project, user)` on ProjectMembership.
- Index Sample by `(project, status)`.
- Index Dataset by `(project, data_format)`.

These indexes support the documented list filtering. Add further indexes only when actual query patterns justify them.

## 7. Implementation notes

- Set `AUTH_USER_MODEL = "accounts.User"` before creating the first migration.
- Use UUIDs for Project, ProjectMembership, Sample, and Dataset. The custom user may retain Django's default primary key.
- Normalize user emails to lowercase before saving; enforce uniqueness at the database level.
- Normalize sample codes by trimming and uppercasing them before saving.
- Add `clean()`/service/serializer validation only where it is actually invoked. Django does not automatically call `full_clean()` on every `save()`.
- Enforce sample status transitions and project immutability in a shared write path used by HTML forms and API serializers.
- Ensure the M2M dataset/sample validation covers API writes, HTML forms, admin actions, and any service entry point that can alter the relation. Override the admin form or make the relation read-only in the admin if the default admin cannot enforce it.
- Reject writes to samples and datasets in `archived` projects in the same shared write path.
- Configure token authentication through `rest_framework.authtoken`.
- Consider a dedicated through model only if the relationship later needs metadata (for example, association type or added date). It is not required for the MVP.

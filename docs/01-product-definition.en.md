# Product Definition — LabTrack

**Document status:** Initial specification
**Version:** 1.1
**Date:** 23 November 2026

## 1. Product summary

LabTrack is a small web application for organizing research projects, laboratory samples, and metadata about datasets associated with those samples.

The MVP focuses on reliable record keeping, clear relationships between records, controlled access, and a straightforward user interface. It does not perform bioinformatics, laboratory instrument integration, scientific computation, or file processing.

## 2. Problem statement

Small research teams may need a simple way to keep project information, sample records, and dataset metadata organized in one place. When these records are tracked separately, it can become harder to find information and understand which samples and datasets belong to a project.

LabTrack provides a single structured interface for these records.

## 3. Goals

1. Allow authenticated users to create and manage research projects.
2. Record samples and their lifecycle status.
3. Register dataset metadata and associate datasets with samples.
4. Ensure users can access only projects they are authorized to see.
5. Provide both a server-rendered web interface and a documented REST API.
6. Demonstrate sound relational modeling, validation, automated testing, and maintainable Django code.

## 4. Non-goals

The MVP will not:
- Analyze biological or genomic data.
- Upload, store, or process large scientific files.
- Integrate with laboratory instruments, sequencing platforms, or external research systems.
- Store patient, participant, clinical, or other sensitive personal data.
- Implement regulatory compliance or claim certification (for example, clinical or laboratory quality standards).
- Implement a React frontend.
- Provide complex workflow automation, audit-grade traceability, or electronic signatures.

For the MVP, `storage_uri` is metadata describing where a dataset would be stored elsewhere; LabTrack does not fetch or validate the referenced resource.

## 5. User roles

### Administrator
- Can view and manage all users and projects.
- Can access all project, sample, and dataset records.
- Can use Django's administrative interface where appropriate.

### Researcher
- Can create projects.
- Can access projects they created or to which they have been added as a member.
- Can create and manage samples and datasets within projects they can access.
- Cannot access another researcher's private project by guessing its URL or API identifier.

The MVP uses two application roles. Django's `is_superuser` remains a separate technical privilege and must not be treated as interchangeable with ordinary researcher access.

## 6. Functional requirements

### 6.1 Accounts and authentication
- Users can log in and log out.
- Each user has an application role: `administrator` or `researcher`. New users default to `researcher`.
- Email is required, unique, and normalized to lowercase.
- Anonymous users cannot access protected project data.
- User creation and role administration are restricted to administrators.
- Administrators can list, create, edit, and deactivate users through the web interface. Routine user administration does not require Django admin.
- User accounts are deactivated rather than deleted from the application UI, preserving records they created. An administrator cannot deactivate their own account or remove their own administrator role.
- Password creation and resets use Django's password validators.
- The first administrator is created with `createsuperuser` and then assigned the `administrator` application role. The application role is independent from Django's technical `is_staff` and `is_superuser` flags.

### 6.2 Projects
Each project has:
- A unique identifier.
- A name.
- A description.
- A status: `active`, `completed`, or `archived`.
- A creator.
- A creation timestamp and an updated timestamp.
- Zero or more researcher members.

Any active authenticated user may create a project. The creator is recorded and cannot be changed. Users with access can view project details. The creator and administrators can manage project settings and membership. Researchers can manage samples and datasets in projects they can access. The exact edit permissions for project metadata must be enforced consistently in HTML views and API endpoints.

Project status rules:
- `active`: normal read and write access.
- `completed`: remains writable; it marks the end of the planned work.
- `archived`: read-only for samples and datasets. Only the creator or an administrator may change project metadata or membership.

Membership rules:
- Additional members must be active users and cannot be the project creator.
- Membership is unique per `(project, user)`.
- Only the creator or an administrator may add or remove members.
- Members cannot remove themselves in the MVP.

A project may be deleted only when it has no samples or datasets.

### 6.3 Samples
Each sample:
- Belongs to exactly one project.
- Has a unique human-readable code within that project.
- Has a sample type.
- Has a collection date (optional if unknown).
- Has a status: `registered`, `processing`, `stored`, `consumed`, or `discarded`.
- May include non-sensitive notes.
- Records its creation and update timestamps.

Sample code rules:
- Codes are trimmed and normalized to uppercase before saving.
- Codes are unique within a project.

Collection dates must not be in the future.

Status transitions:
- `registered` → `processing`, `stored`, `discarded`
- `processing` → `stored`, `consumed`, `discarded`
- `stored` → `processing`, `consumed`, `discarded`
- `consumed` and `discarded` are terminal states.

A sample's project cannot be changed after creation in the MVP. This avoids silently moving sample records between projects. `created_by` is set from the authenticated user and is never accepted from client input.

Samples cannot be created, updated, or deleted while their project is `archived`.

### 6.4 Datasets
Each dataset:
- Belongs to exactly one project.
- Has a name and description.
- Has a format label (for example, `FASTQ`, `FASTA`, `CSV`, or `OTHER`).
- Has a `storage_uri` string describing an external storage location; no file is uploaded by the MVP.
- May be associated with zero or more samples from the same project.
- Records who created it and when it was registered.

A dataset may be associated with multiple samples because a dataset can represent combined or derived data. Cross-project sample associations must be rejected.

Dataset rules:
- A dataset's project cannot be changed after creation.
- Dataset names need not be unique within a project.
- `storage_uri` is a `CharField` of bounded length. It is untrusted metadata: never fetched automatically and never rendered as a clickable link.
- `created_by` is set from the authenticated user and is never accepted from client input.
- All associated samples must belong to the dataset's project. Validate this on every write path, including API, HTML forms, and Django admin.

Datasets cannot be created, updated, or deleted while their project is `archived`.

### 6.5 Dashboard
The dashboard displays basic counts for projects, samples, and datasets that the current user is authorized to access. It may show recently updated records. It must not reveal counts or names from inaccessible projects.

### 6.6 Search and filtering
Users can search and filter within their authorized data:
- Projects by name and status.
- Samples by code, type, and status.
- Datasets by name and format.

Pagination must be used for API list endpoints. Search results must respect project-level authorization.

### 6.7 API access
- The API is exposed under a versioned prefix (`/api/v1/`).
- Core resources are exposed at `/api/v1/projects/`, `/api/v1/memberships/`, `/api/v1/samples/`, and `/api/v1/datasets/`. Clients obtain a token from `/api/v1/auth/token/`.
- Project membership create and delete operations are restricted to the project creator or an administrator.
- Authentication uses session authentication for the browsable API and token authentication for independent clients.
- All resource endpoints require authentication. The token endpoint accepts username and password credentials.
- List endpoints are paginated with a default page size of 20.
- Filtering is implemented with explicit query parameters; no additional filtering dependency is required for the MVP.
- Dataset format filtering uses the `data_format` query parameter because `format` is reserved by Django REST Framework for response format selection.
- Inaccessible records return the same not-found response as records that do not exist.

## 7. Quality requirements

- Authorization is enforced server-side in both HTML and API layers.
- Data integrity is protected by database constraints where possible and application validation for cross-record rules.
- Passwords are handled by Django's authentication system.
- Secrets are supplied through environment variables and are never committed.
- Datetimes are timezone-aware.
- Automated tests cover permissions, validation, and core workflows.
- The application is maintainable, documented, and runnable locally using the documented setup.

## 8. MVP acceptance criteria

The MVP is considered complete only when:
1. A user can authenticate and see only authorized projects.
2. An administrator can access all projects.
3. A researcher can create a project and add members.
4. Authorized users can create, view, update, and delete samples according to the documented rules.
5. Authorized users can register datasets and associate samples from the same project.
6. Cross-project dataset/sample associations are rejected by both API and HTML workflows where applicable.
7. Search and filters do not bypass authorization.
8. API list endpoints are paginated.
9. Automated tests cover the above access and validation rules.
10. Django checks pass and the project can be started from a clean checkout using the README.
11. Archived projects reject sample and dataset writes.
12. Sample status changes follow the documented lifecycle.
13. API clients can authenticate with session or token credentials.
14. An administrator can create, edit, and deactivate users from the web interface.

## 9. Risks and open questions

- This is a portfolio demonstrator, not a real LIMS. Domain terminology and workflow are intentionally simplified.
- The MVP does not store scientific files; it stores metadata and an external location string.
- A future real-world deployment would require security review, backups, monitoring, data-retention rules, audit requirements, and domain validation with actual researchers.
- The final license and hosting provider have not been selected.

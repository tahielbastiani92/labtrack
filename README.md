# LabTrack

**Research Sample Management System — portfolio demonstrator**

LabTrack is an independent web application concept for organizing research projects, laboratory samples, and related datasets. It is being built as a software-development portfolio project to demonstrate Python, Django, Django REST Framework, relational data modeling, automated testing, and practical engineering workflows.

> **Status:** Design and specification phase. Features described below are planned until implemented and tested.
>
> **Important:** LabTrack is a fictional demonstrator. It is not a certified LIMS, does not perform scientific analysis, and is not intended for clinical, diagnostic, or regulated research use.

## Planned MVP

- User authentication and role-based access (administrator/researcher).
- Research project creation and membership.
- Sample registration and status tracking.
- Dataset metadata linked to projects and samples.
- Search and filtering.
- A dashboard with basic operational counts.
- HTML interface using Django templates and Bootstrap.
- REST API using Django REST Framework.
- Automated tests, Docker-based local development, and CI.

## Technology direction

- Python 3.13
- Django 6.1.x
- Django REST Framework 3.18.x
- PostgreSQL 17
- `uv`
- Django templates, Bootstrap 5, vanilla JavaScript
- Pytest / pytest-django
- Docker Compose
- GitHub Actions

Versions are selected based on the compatibility information available during the project design (November 2026). Use current compatible patch releases within the selected minor series.

## Documentation

- [Product definition (English)](docs/01-product-definition.en.md)
- [Definición del producto (Español)](docs/01-product-definition.es.md)
- [Data model (English)](docs/02-data-model.en.md)
- [Modelo de datos (Español)](docs/02-data-model.es.md)
- [Architecture decisions (English)](docs/03-architecture-decisions.en.md)

## Project status

| Area | Status |
|---|---|
| Product scope | Specified |
| Initial data model | Specified |
| Architecture decisions | Specified |
| Django implementation | Not started |
| Automated tests | Not started |
| Deployment | Not started |

## Safety and demo data

Only synthetic data may be committed. Never commit secrets, real research or participant data, institutional records, database dumps, or code from third-party/client projects.

## License

A license has not yet been selected. Do not add a license until the repository owner chooses one. Making a GitHub repository public without a license does not automatically grant broad reuse rights to others.

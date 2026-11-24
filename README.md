# LabTrack

**Research Sample Management System — Portfolio Demonstrator**

LabTrack is an independent web application for organizing research projects, laboratory samples, and related datasets.

It was developed as a software engineering portfolio project to demonstrate practical experience with Python, Django, Django REST Framework, relational data modeling, automated testing, and application deployment.

**Live demo:** [https://labtrack-8zwv.onrender.com/](https://labtrack-8zwv.onrender.com/)
**Source code:** [https://github.com/tahielbastiani92/labtrack](https://github.com/tahielbastiani92/labtrack)

> **Demo access:** A demonstration administrator account is available. Contact the project author for the login credentials.

> **Important:** LabTrack is a fictional demonstrator, not a certified Laboratory Information Management System (LIMS). It does not perform scientific analysis and is not intended for clinical, diagnostic, or regulated research use.

## Features

- User authentication and role-based access control (administrator/researcher).
- Research project creation and management.
- Project membership management.
- Laboratory sample registration and status tracking.
- Dataset metadata management and sample relationships.
- Search, filtering, and paginated results.
- Dashboard with operational summaries.
- HTML interface built with Django templates and Bootstrap.
- REST API built with Django REST Framework.
- Automated tests for domain logic, permissions, HTML workflows, administration, and API endpoints.

## Technology Stack

| Area                    | Technologies                                      |
| ----------------------- | ------------------------------------------------- |
| Backend                 | Python 3.13, Django 6.1                           |
| REST API                | Django REST Framework 3.18                        |
| Database                | PostgreSQL 17                                     |
| Frontend                | Django Templates, Bootstrap 5, vanilla JavaScript |
| Testing                 | Pytest, pytest-django                             |
| Code quality            | Ruff                                              |
| Dependency management   | uv                                                |
| Development environment | Docker Compose                                    |
| CI                      | GitHub Actions                                    |
| Deployment              | Render, Neon PostgreSQL                           |

The application uses Django's server-rendered templates rather than a separate React frontend. JavaScript is used for client-side interactions.

## Application Structure

The project is organized into Django applications:

- `accounts`: custom user model, authentication, and application roles.
- `projects`: research projects, memberships, and project-level permissions.
- `samples`: sample registration, management, and status transitions.
- `datasets`: dataset metadata and relationships with projects and samples.

The application distinguishes between Django's built-in staff/superuser permissions and its own application-level roles.

Project visibility and management permissions are enforced at the application level. Dataset relationships are validated to ensure that associated samples belong to the same project.

## Architecture and Documentation

The repository includes additional documentation covering the product scope, data model, and architectural decisions:

- [Product definition](docs/01-product-definition.en.md)
- [Data model](docs/02-data-model.en.md)
- [Architecture decisions](docs/03-architecture-decisions.en.md)

## REST API

The API is available under `/api/v1/`.

Core endpoints:

| Resource       | Endpoint                   |
| -------------- | -------------------------- |
| Authentication | `POST /api/v1/auth/token/` |
| Projects       | `/api/v1/projects/`        |
| Memberships    | `/api/v1/memberships/`     |
| Samples        | `/api/v1/samples/`         |
| Datasets       | `/api/v1/datasets/`        |

The API supports session authentication and token authentication. Resource endpoints require authentication and use pagination with 20 records per page.

Supported query parameters include:

- **Projects:** `q` (name), `status`.
- **Memberships:** `project` (UUID).
- **Samples:** `q` (code), `type`, `status`, `project` (UUID).
- **Datasets:** `q` (name), `data_format`, `project` (UUID).

Membership creation and deletion are restricted to project creators and administrators. Access to unavailable resources follows consistent permission-handling rules.

## Testing and Code Quality

The project includes automated tests covering:

- Domain models and validation rules.
- Role-based permissions.
- Project and membership workflows.
- Sample and dataset relationships.
- HTML views and forms.
- Administrative user management.
- REST API behavior and authentication.
- Demo data loading and idempotency.

Run the checks locally:

```bash
uv run pytest
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
```

The test suite and CI use PostgreSQL 17, matching the database engine used in development and production.

## Demo Environment

The application is deployed on Render and uses Neon as its PostgreSQL database provider.

- **Application:** [https://labtrack-8zwv.onrender.com/](https://labtrack-8zwv.onrender.com/)
- **Database:** Neon PostgreSQL.
- **Demo content:** Synthetic users, research projects, samples, and datasets.

The free Render service may spin down after a period of inactivity. Consequently, the first request after inactivity can take longer than usual.

## Local Development

Running the application locally is not required to explore the live demo.

The project provides a Docker Compose environment that runs both the Django application and PostgreSQL database as separate services.

### Prerequisites

- Docker
- Docker Compose

### Run with Docker Compose

Clone the repository and configure the environment:

```bash
git clone https://github.com/tahielbastiani92/labtrack.git
cd labtrack

cp .env.example .env
docker compose up --build
```

Docker Compose starts two services:

- **web:** Django application, running on port `8000`.
- **db:** PostgreSQL 17 database, exposed on host port `5434`.

Database migrations are applied automatically when the web container starts.

The application is available at:

**http://localhost:8000/**

To create the initial administrator account:

```bash
docker compose exec web python manage.py createsuperuser
```

After creating the superuser, assign the application role `administrator` through the Django admin or shell. The application role is independent of Django's `is_staff` and `is_superuser` flags.

To stop the services:

```bash
docker compose down
```

To stop the services and remove the local database volume:

```bash
docker compose down -v
```

**Note:** The last command permanently deletes the local PostgreSQL data.

### Run Django Directly (Alternative)

Developers who prefer not to run the Django application in Docker can use `uv` locally while keeping PostgreSQL in Docker.

Prerequisites:

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Docker with Docker Compose

```bash
cp .env.example .env
uv sync
docker compose up -d db
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

The Django development server is available at **http://localhost:8000/**.

## Project Status

The MVP implementation is complete and deployed.

| Area                                      | Status      |
| ----------------------------------------- | ----------- |
| Product scope and architecture            | Completed   |
| Data models and migrations                | Completed   |
| Authentication and role-based permissions | Implemented |
| Project and membership workflows          | Implemented |
| Sample management                         | Implemented |
| Dataset management                        | Implemented |
| HTML interface                            | Implemented |
| REST API                                  | Implemented |
| Automated tests                           | Implemented |
| CI workflow                               | Configured  |
| Production deployment                     | Live        |

## Safety and Demo Data

LabTrack uses synthetic demonstration data only.

No real research data, participant information, institutional records, client data, or third-party proprietary code should be committed to this repository.

Never commit environment files containing secrets, database credentials, API tokens, or production configuration.

## License

No license has been selected for this project yet.

Making this repository public does not automatically grant permission to reuse, distribute, or modify its contents.

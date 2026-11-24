import json
import os
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.datasets.models import Dataset
from apps.projects.models import Project, ProjectMembership
from apps.samples.models import Sample


class Command(BaseCommand):
    help = "Load synthetic demonstration data without modifying existing records."

    def handle(self, *args, **options):
        fixture_path = Path(settings.BASE_DIR) / "fixtures" / "demo_data.json"

        if not fixture_path.exists():
            raise CommandError(f"Fixture not found: {fixture_path}")

        try:
            with fixture_path.open(encoding="utf-8") as fixture:
                data = json.load(fixture)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Could not read fixture: {exc}") from exc

        self.validate_fixture(data)

        password = os.environ.get("DEMO_USERS_PASSWORD")
        if not password:
            raise CommandError(
                "Set the DEMO_USERS_PASSWORD environment variable before "
                "loading demo data."
            )

        with transaction.atomic():
            users = self.load_users(data["users"], password)
            projects = self.load_projects(data["projects"], users)
            samples = self.load_samples(data["samples"], users, projects)
            self.load_datasets(data["datasets"], users, projects, samples)

        self.stdout.write(
            self.style.SUCCESS("Demo data loaded successfully.")
        )

    def validate_fixture(self, data):
        required_sections = {"users", "projects", "samples", "datasets"}

        if not isinstance(data, dict) or set(data) != required_sections:
            raise CommandError(
                "Fixture must contain exactly: users, projects, samples and datasets."
            )

        for section in required_sections:
            if not isinstance(data[section], list):
                raise CommandError(f"'{section}' must be a list.")

        usernames = set()
        emails = set()

        for user in data["users"]:
            self.require_fields(
                user,
                ("username", "email", "first_name", "last_name", "role"),
                "user",
            )

            if user["username"] in usernames:
                raise CommandError(f"Duplicate username: {user['username']}")

            if user["email"].lower() in emails:
                raise CommandError(f"Duplicate email: {user['email']}")

            if user["role"] not in ("administrator", "researcher"):
                raise CommandError(f"Invalid role for user: {user['username']}")

            usernames.add(user["username"])
            emails.add(user["email"].lower())

        project_names = set()

        for project in data["projects"]:
            self.require_fields(
                project,
                ("name", "description", "status", "created_by", "members"),
                "project",
            )

            if project["name"] in project_names:
                raise CommandError(f"Duplicate project: {project['name']}")

            if project["status"] not in Project.Status.values:
                raise CommandError(f"Invalid status in project: {project['name']}")

            if project["created_by"] not in usernames:
                raise CommandError(
                    f"Unknown project creator: {project['created_by']}"
                )

            if not set(project["members"]).issubset(usernames):
                raise CommandError(
                    f"Unknown member in project: {project['name']}"
                )

            project_names.add(project["name"])

        sample_keys = set()

        for sample in data["samples"]:
            self.require_fields(
                sample,
                (
                    "code",
                    "project",
                    "sample_type",
                    "collection_date",
                    "status",
                    "notes",
                    "created_by",
                ),
                "sample",
            )

            key = (sample["project"], sample["code"].strip().upper())

            if key in sample_keys:
                raise CommandError(f"Duplicate sample: {key}")

            if sample["project"] not in project_names:
                raise CommandError(
                    f"Unknown project in sample: {sample['project']}"
                )

            if sample["created_by"] not in usernames:
                raise CommandError(
                    f"Unknown sample creator: {sample['created_by']}"
                )

            if sample["status"] not in Sample.Status.values:
                raise CommandError(f"Invalid status in sample: {sample['code']}")


            try:
                date.fromisoformat(sample["collection_date"])
            except (TypeError, ValueError) as exc:
                raise CommandError(
                    f"Invalid collection date in sample: {sample['code']}"
                ) from exc

            sample_keys.add(key)

        dataset_keys = set()

        for dataset in data["datasets"]:
            self.require_fields(
                dataset,
                (
                    "name",
                    "project",
                    "description",
                    "data_format",
                    "storage_uri",
                    "samples",
                    "created_by",
                ),
                "dataset",
            )

            key = (dataset["project"], dataset["name"])

            if key in dataset_keys:
                raise CommandError(f"Duplicate dataset: {key}")

            if dataset["project"] not in project_names:
                raise CommandError(
                    f"Unknown project in dataset: {dataset['name']}"
                )

            if dataset["created_by"] not in usernames:
                raise CommandError(
                    f"Unknown dataset creator: {dataset['created_by']}"
                )

            if dataset["data_format"] not in Dataset.DataFormat.values:
                raise CommandError(
                    f"Invalid data format in dataset: {dataset['name']}"
                )

            for sample_code in dataset["samples"]:
                if (dataset["project"], sample_code.upper()) not in sample_keys:
                    raise CommandError(
                        f"Sample '{sample_code}' does not belong to "
                        f"dataset project '{dataset['project']}'."
                    )

            dataset_keys.add(key)

    @staticmethod
    def require_fields(record, fields, record_type):
        if not isinstance(record, dict):
            raise CommandError(f"Each {record_type} must be an object.")

        missing = set(fields) - record.keys()

        if missing:
            raise CommandError(
                f"Missing fields in {record_type}: {', '.join(sorted(missing))}"
            )

    def load_users(self, records, password):
        User = get_user_model()
        users = {}

        for record in records:
            username = record["username"]
            email = record["email"].strip().lower()

            user = User.objects.filter(username=username).first()

            if user:
                if user.email.lower() != email:
                    raise CommandError(
                        f"Username '{username}' already exists with another email."
                    )

                self.stdout.write(f"Reusing existing user: {username}")
            else:
                email_owner = User.objects.filter(email__iexact=email).first()

                if email_owner:
                    raise CommandError(
                        f"Email '{email}' already belongs to another user."
                    )

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=record["first_name"],
                    last_name=record["last_name"],
                    role=record["role"],
                )

                self.stdout.write(f"Created user: {username}")

            users[username] = user

        return users

    def load_projects(self, records, users):
        projects = {}

        for record in records:
            name = record["name"]
            creator = users[record["created_by"]]

            matches = Project.objects.filter(name=name)

            if matches.count() > 1:
                raise CommandError(f"Multiple projects found with name: {name}")

            project = matches.first()

            if project:
                if project.created_by_id != creator.pk:
                    raise CommandError(
                        f"Project '{name}' already exists with another creator."
                    )

                self.stdout.write(f"Reusing existing project: {name}")
            else:
                project = Project.objects.create(
                    name=name,
                    description=record["description"],
                    status=record["status"],
                    created_by=creator,
                )

                for username in record["members"]:
                    ProjectMembership.objects.create(
                        project=project,
                        user=users[username],
                    )

                self.stdout.write(f"Created project: {name}")

            projects[name] = project

        return projects

    def load_samples(self, records, users, projects):
        samples = {}

        for record in records:
            project = projects[record["project"]]
            code = record["code"].strip().upper()

            sample, created = Sample.objects.get_or_create(
                project=project,
                code=code,
                defaults={
                    "sample_type": record["sample_type"],
                    "collection_date": record["collection_date"],
                    "status": record["status"],
                    "notes": record["notes"],
                    "created_by": users[record["created_by"]],
                },
            )

            action = "Created" if created else "Reusing existing"
            self.stdout.write(f"{action} sample: {code}")

            samples[(record["project"], code)] = sample

        return samples

    def load_datasets(self, records, users, projects, samples):
        for record in records:
            project = projects[record["project"]]
            name = record["name"]

            matches = Dataset.objects.filter(project=project, name=name)

            if matches.count() > 1:
                raise CommandError(
                    f"Multiple datasets found with name: {name}"
                )

            dataset = matches.first()

            if dataset:
                self.stdout.write(f"Reusing existing dataset: {name}")
                continue

            dataset = Dataset.objects.create(
                project=project,
                name=name,
                description=record["description"],
                data_format=record["data_format"],
                storage_uri=record["storage_uri"],
                created_by=users[record["created_by"]],
            )

            dataset.samples.set(
                samples[(record["project"], code.upper())]
                for code in record["samples"]
            )

            self.stdout.write(f"Created dataset: {name}")
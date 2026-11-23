from django.core.exceptions import ValidationError


def validate_samples_belong_to_project(project, samples) -> None:
    invalid = [sample.code for sample in samples or [] if sample.project_id != project.pk]
    if invalid:
        raise ValidationError(
            "All samples must belong to the dataset's project: " + ", ".join(sorted(invalid))
        )

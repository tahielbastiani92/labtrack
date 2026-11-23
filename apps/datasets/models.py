import uuid

from django.conf import settings
from django.db import models

from apps.projects.models import Project
from apps.samples.models import Sample


class Dataset(models.Model):
    class DataFormat(models.TextChoices):
        FASTQ = "FASTQ", "FASTQ"
        FASTA = "FASTA", "FASTA"
        CSV = "CSV", "CSV"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name="datasets",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    data_format = models.CharField(
        max_length=20,
        choices=DataFormat.choices,
        default=DataFormat.OTHER,
    )
    storage_uri = models.CharField(max_length=2048, blank=True)
    samples = models.ManyToManyField(
        Sample,
        related_name="datasets",
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_datasets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("project", "data_format"), name="dataset_project_format_idx"),
        ]

    def __str__(self) -> str:
        return self.name

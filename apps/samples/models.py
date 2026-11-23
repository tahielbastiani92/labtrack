import uuid

from django.conf import settings
from django.db import models

from apps.projects.models import Project


class Sample(models.Model):
    class Status(models.TextChoices):
        REGISTERED = "registered", "Registered"
        PROCESSING = "processing", "Processing"
        STORED = "stored", "Stored"
        CONSUMED = "consumed", "Consumed"
        DISCARDED = "discarded", "Discarded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name="samples",
    )
    code = models.CharField(max_length=100)
    sample_type = models.CharField(max_length=100)
    collection_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REGISTERED,
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_samples",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("project", "code"),
                name="unique_sample_code_per_project",
            )
        ]
        indexes = [
            models.Index(fields=("project", "status"), name="sample_project_status_idx"),
        ]

    def __str__(self) -> str:
        return self.code

    def save(self, *args, **kwargs) -> None:
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

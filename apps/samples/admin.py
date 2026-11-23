from django.contrib import admin

from .forms import SampleAdminForm
from .models import Sample


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    form = SampleAdminForm
    list_display = ("code", "project", "sample_type", "status", "created_at")
    list_filter = ("status", "sample_type")
    search_fields = ("code", "notes")
    autocomplete_fields = ("project", "created_by")

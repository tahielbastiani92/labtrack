from django.contrib import admin

from .forms import DatasetAdminForm
from .models import Dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    form = DatasetAdminForm
    list_display = ("name", "project", "data_format", "created_at")
    list_filter = ("data_format",)
    search_fields = ("name", "description")
    autocomplete_fields = ("project", "samples", "created_by")

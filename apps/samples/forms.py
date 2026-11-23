from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.projects.access import project_is_writable
from config.forms import BootstrapFormMixin

from .models import Sample
from .rules import validate_status_transition


class SampleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Sample
        fields = ("code", "sample_type", "collection_date", "status", "notes")
        widgets = {
            "collection_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, project=None, user=None, **kwargs) -> None:
        self.project = project
        self.user = user
        super().__init__(*args, **kwargs)
        if self.instance._state.adding:
            self.fields.pop("status", None)

    def clean_collection_date(self):
        value = self.cleaned_data.get("collection_date")
        if value and value > timezone.localdate():
            raise forms.ValidationError("Collection date cannot be in the future.")
        return value

    def clean_status(self):
        value = self.cleaned_data.get("status")
        if not self.instance._state.adding and value and value != self.instance.status:
            try:
                validate_status_transition(self.instance.status, value)
            except ValidationError as exc:
                raise forms.ValidationError(exc.messages) from exc
        return value

    def clean(self):
        cleaned_data = super().clean()
        if self.project is not None and not project_is_writable(self.project):
            raise forms.ValidationError("Archived projects are read-only.")
        return cleaned_data


class SampleAdminForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = (
            "project",
            "code",
            "sample_type",
            "collection_date",
            "status",
            "notes",
            "created_by",
        )

    def clean_collection_date(self):
        value = self.cleaned_data.get("collection_date")
        if value and value > timezone.localdate():
            raise forms.ValidationError("Collection date cannot be in the future.")
        return value

    def clean_status(self):
        value = self.cleaned_data.get("status")
        if not self.instance._state.adding and value and value != self.instance.status:
            try:
                validate_status_transition(self.instance.status, value)
            except ValidationError as exc:
                raise forms.ValidationError(exc.messages) from exc
        return value

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get("project") or self.instance.project
        if project is not None and not project_is_writable(project):
            raise forms.ValidationError("Archived projects are read-only.")
        return cleaned_data

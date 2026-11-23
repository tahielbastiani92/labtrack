from django import forms
from django.core.exceptions import ValidationError

from apps.projects.access import project_is_writable
from apps.samples.models import Sample
from config.forms import BootstrapFormMixin

from .models import Dataset
from .rules import validate_samples_belong_to_project


class DatasetForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ("name", "description", "data_format", "storage_uri", "samples")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "samples": forms.SelectMultiple(attrs={"size": 8}),
        }

    def __init__(self, *args, project=None, user=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.project = project or self.instance.project
        self.user = user
        if self.project is not None:
            self.fields["samples"].queryset = Sample.objects.filter(
                project=self.project
            ).order_by("code")
        else:
            self.fields["samples"].queryset = Sample.objects.none()

    def clean_samples(self):
        samples = self.cleaned_data.get("samples")
        if self.project is not None:
            try:
                validate_samples_belong_to_project(self.project, samples)
            except ValidationError as exc:
                raise forms.ValidationError(exc.messages) from exc
        return samples

    def clean(self):
        cleaned_data = super().clean()
        if self.project is not None and not project_is_writable(self.project):
            raise forms.ValidationError("Archived projects are read-only.")
        return cleaned_data


class DatasetAdminForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = (
            "project",
            "name",
            "description",
            "data_format",
            "storage_uri",
            "samples",
            "created_by",
        )

    def clean_samples(self):
        project = self.cleaned_data.get("project") or self.instance.project
        samples = self.cleaned_data.get("samples")
        if project is not None:
            try:
                validate_samples_belong_to_project(project, samples)
            except ValidationError as exc:
                raise forms.ValidationError(exc.messages) from exc
        return samples

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get("project") or self.instance.project
        if project is not None and not project_is_writable(project):
            raise forms.ValidationError("Archived projects are read-only.")
        return cleaned_data

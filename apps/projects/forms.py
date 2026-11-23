from django import forms
from django.contrib.auth import get_user_model

from config.forms import BootstrapFormMixin

from .models import Project, ProjectMembership

User = get_user_model()


class ProjectForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "status")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class ProjectMembershipForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ProjectMembership
        fields = ("user",)

    def __init__(self, *args, project=None, **kwargs) -> None:
        self.project = project
        super().__init__(*args, **kwargs)
        users = User.objects.filter(is_active=True)
        if project is not None:
            users = users.exclude(pk=project.created_by_id).exclude(
                project_memberships__project=project
            )
        self.fields["user"].queryset = users.order_by("username")

    def clean_user(self):
        user = self.cleaned_data["user"]
        if self.project is not None and user.pk == self.project.created_by_id:
            raise forms.ValidationError("The project creator already has access.")
        return user

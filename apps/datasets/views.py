from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.projects.access import get_visible_project, project_is_writable, projects_visible_to
from config.utils import parse_uuid

from .forms import DatasetForm
from .models import Dataset
from .selectors import datasets_visible_to


class DatasetListView(LoginRequiredMixin, ListView):
    model = Dataset
    template_name = "datasets/list.html"
    context_object_name = "datasets"
    paginate_by = 20

    def get_queryset(self):
        queryset = datasets_visible_to(self.request.user).select_related(
            "project", "created_by"
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        data_format = self.request.GET.get("format", "")
        if data_format in Dataset.DataFormat.values:
            queryset = queryset.filter(data_format=data_format)
        project_id = parse_uuid(self.request.GET.get("project"))
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["format_choices"] = Dataset.DataFormat.choices
        context["current_q"] = self.request.GET.get("q", "")
        context["current_format"] = self.request.GET.get("format", "")
        context["current_project"] = self.request.GET.get("project", "")
        project_id = parse_uuid(self.request.GET.get("project"))
        if project_id:
            context["current_project_obj"] = (
                projects_visible_to(self.request.user).filter(pk=project_id).first()
            )
        return context


class DatasetDetailView(LoginRequiredMixin, DetailView):
    model = Dataset
    template_name = "datasets/detail.html"
    context_object_name = "dataset"

    def get_queryset(self):
        return datasets_visible_to(self.request.user).select_related(
            "project", "created_by"
        ).prefetch_related("samples")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_write"] = project_is_writable(self.object.project)
        return context


class DatasetCreateView(LoginRequiredMixin, CreateView):
    model = Dataset
    form_class = DatasetForm
    template_name = "datasets/form.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.project = get_visible_project(request.user, kwargs["project_pk"])
            if not project_is_writable(self.project):
                raise PermissionDenied("Archived projects are read-only.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.created_by = self.request.user
        messages.success(self.request, "Dataset registered.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("datasets:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Register dataset in {self.project.name}"
        context["submit_label"] = "Register dataset"
        context["cancel_url"] = reverse("projects:detail", kwargs={"pk": self.project.pk})
        context["project"] = self.project
        return context


class DatasetUpdateView(LoginRequiredMixin, UpdateView):
    model = Dataset
    form_class = DatasetForm
    template_name = "datasets/form.html"

    def get_queryset(self):
        return datasets_visible_to(self.request.user)

    def get_object(self, queryset=None):
        dataset = super().get_object(queryset)
        if not project_is_writable(dataset.project):
            raise PermissionDenied("Archived projects are read-only.")
        return dataset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.object.project
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Dataset updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("datasets:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit dataset"
        context["submit_label"] = "Save changes"
        context["cancel_url"] = reverse("datasets:detail", kwargs={"pk": self.object.pk})
        context["project"] = self.object.project
        return context


class DatasetDeleteView(LoginRequiredMixin, DeleteView):
    model = Dataset
    template_name = "confirm_delete.html"

    def get_queryset(self):
        return datasets_visible_to(self.request.user)

    def get_object(self, queryset=None):
        dataset = super().get_object(queryset)
        if not project_is_writable(dataset.project):
            raise PermissionDenied("Archived projects are read-only.")
        return dataset

    def form_valid(self, form):
        messages.success(self.request, "Dataset deleted.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("datasets:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete dataset"
        context["cancel_url"] = reverse("datasets:detail", kwargs={"pk": self.object.pk})
        return context

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.projects.access import get_visible_project, project_is_writable, projects_visible_to
from config.utils import parse_uuid

from .forms import SampleForm
from .models import Sample
from .selectors import samples_visible_to


class SampleListView(LoginRequiredMixin, ListView):
    model = Sample
    template_name = "samples/list.html"
    context_object_name = "samples"
    paginate_by = 20

    def get_queryset(self):
        queryset = samples_visible_to(self.request.user).select_related(
            "project", "created_by"
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(code__icontains=query)
        sample_type = self.request.GET.get("type", "").strip()
        if sample_type:
            queryset = queryset.filter(sample_type__icontains=sample_type)
        status = self.request.GET.get("status", "")
        if status in Sample.Status.values:
            queryset = queryset.filter(status=status)
        project_id = parse_uuid(self.request.GET.get("project"))
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Sample.Status.choices
        context["current_q"] = self.request.GET.get("q", "")
        context["current_type"] = self.request.GET.get("type", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["current_project"] = self.request.GET.get("project", "")
        project_id = parse_uuid(self.request.GET.get("project"))
        if project_id:
            context["current_project_obj"] = (
                projects_visible_to(self.request.user).filter(pk=project_id).first()
            )
        return context


class SampleDetailView(LoginRequiredMixin, DetailView):
    model = Sample
    template_name = "samples/detail.html"
    context_object_name = "sample"

    def get_queryset(self):
        return samples_visible_to(self.request.user).select_related(
            "project", "created_by"
        ).prefetch_related("datasets")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_write"] = project_is_writable(self.object.project)
        return context


class SampleCreateView(LoginRequiredMixin, CreateView):
    model = Sample
    form_class = SampleForm
    template_name = "samples/form.html"

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
        messages.success(self.request, "Sample registered.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("samples:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Register sample in {self.project.name}"
        context["submit_label"] = "Register sample"
        context["cancel_url"] = reverse("projects:detail", kwargs={"pk": self.project.pk})
        context["project"] = self.project
        return context


class SampleUpdateView(LoginRequiredMixin, UpdateView):
    model = Sample
    form_class = SampleForm
    template_name = "samples/form.html"

    def get_queryset(self):
        return samples_visible_to(self.request.user)

    def get_object(self, queryset=None):
        sample = super().get_object(queryset)
        if not project_is_writable(sample.project):
            raise PermissionDenied("Archived projects are read-only.")
        return sample

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.object.project
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Sample updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("samples:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit sample"
        context["submit_label"] = "Save changes"
        context["cancel_url"] = reverse("samples:detail", kwargs={"pk": self.object.pk})
        context["project"] = self.object.project
        return context


class SampleDeleteView(LoginRequiredMixin, DeleteView):
    model = Sample
    template_name = "confirm_delete.html"

    def get_queryset(self):
        return samples_visible_to(self.request.user)

    def get_object(self, queryset=None):
        sample = super().get_object(queryset)
        if not project_is_writable(sample.project):
            raise PermissionDenied("Archived projects are read-only.")
        return sample

    def form_valid(self, form):
        messages.success(self.request, "Sample deleted.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("samples:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete sample"
        context["cancel_url"] = reverse("samples:detail", kwargs={"pk": self.object.pk})
        return context

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .access import (
    can_manage_project,
    get_visible_project,
    project_is_writable,
    projects_visible_to,
)
from .forms import ProjectForm, ProjectMembershipForm
from .models import Project, ProjectMembership


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/list.html"
    context_object_name = "projects"
    paginate_by = 20

    def get_queryset(self):
        queryset = projects_visible_to(self.request.user).select_related("created_by")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        status = self.request.GET.get("status", "")
        if status in Project.Status.values:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Project.Status.choices
        context["current_q"] = self.request.GET.get("q", "")
        context["current_status"] = self.request.GET.get("status", "")
        return context


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "projects/detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return projects_visible_to(self.request.user).select_related("created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        context["can_manage"] = can_manage_project(self.request.user, project)
        context["can_write"] = project_is_writable(project)
        context["memberships"] = project.memberships.select_related("user").order_by("joined_at")
        context["samples"] = (
            project.samples.select_related("created_by").order_by("-created_at")[:10]
        )
        context["datasets"] = (
            project.datasets.select_related("created_by")
            .prefetch_related("samples")
            .order_by("-created_at")[:10]
        )
        context["membership_form"] = ProjectMembershipForm(project=project)
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Project created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("projects:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New project"
        context["submit_label"] = "Create project"
        context["cancel_url"] = reverse("projects:list")
        return context


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/form.html"

    def get_queryset(self):
        return projects_visible_to(self.request.user)

    def get_object(self, queryset=None):
        project = super().get_object(queryset)
        if not can_manage_project(self.request.user, project):
            raise PermissionDenied
        return project

    def form_valid(self, form):
        messages.success(self.request, "Project updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("projects:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit project"
        context["submit_label"] = "Save changes"
        context["cancel_url"] = reverse("projects:detail", kwargs={"pk": self.object.pk})
        return context


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = "confirm_delete.html"

    def get_queryset(self):
        return projects_visible_to(self.request.user)

    def get_object(self, queryset=None):
        project = super().get_object(queryset)
        if not can_manage_project(self.request.user, project):
            raise PermissionDenied
        return project

    def form_valid(self, form):
        if self.object.samples.exists() or self.object.datasets.exists():
            messages.error(
                self.request,
                "Delete the project's samples and datasets before deleting the project.",
            )
            return redirect("projects:detail", pk=self.object.pk)
        messages.success(self.request, "Project deleted.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("projects:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete project"
        context["cancel_url"] = reverse("projects:detail", kwargs={"pk": self.object.pk})
        return context


@login_required
@require_POST
def membership_add(request, pk):
    project = get_visible_project(request.user, pk)
    if not can_manage_project(request.user, project):
        raise PermissionDenied

    form = ProjectMembershipForm(
        request.POST,
        project=project,
        instance=ProjectMembership(project=project),
    )
    if form.is_valid():
        form.save()
        messages.success(request, "Member added.")
    else:
        messages.error(request, "Could not add member. Check the selected user.")
    return redirect("projects:detail", pk=project.pk)


@login_required
@require_POST
def membership_remove(request, pk, membership_pk):
    project = get_visible_project(request.user, pk)
    if not can_manage_project(request.user, project):
        raise PermissionDenied

    membership = get_object_or_404(project.memberships, pk=membership_pk)
    membership.delete()
    messages.success(request, "Member removed.")
    return redirect("projects:detail", pk=project.pk)

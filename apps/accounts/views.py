import logging

from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView

from .access import AdministratorRequiredMixin
from .forms import AdminUserCreateForm, AdminUserUpdateForm
from .models import User

logger = logging.getLogger(__name__)


class UserListView(AdministratorRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.order_by("username")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        role = self.request.GET.get("role", "")
        if role in User.Role.values:
            queryset = queryset.filter(role=role)
        active = self.request.GET.get("active", "")
        if active == "1":
            queryset = queryset.filter(is_active=True)
        elif active == "0":
            queryset = queryset.filter(is_active=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role_choices"] = User.Role.choices
        context["current_q"] = self.request.GET.get("q", "")
        context["current_role"] = self.request.GET.get("role", "")
        context["current_active"] = self.request.GET.get("active", "")
        return context


class UserCreateView(AdministratorRequiredMixin, CreateView):
    model = User
    form_class = AdminUserCreateForm
    template_name = "accounts/user_form.html"

    def form_valid(self, form):
        messages.success(self.request, "User created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("accounts:user_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New user"
        context["submit_label"] = "Create user"
        context["cancel_url"] = reverse("accounts:user_list")
        return context


class UserUpdateView(AdministratorRequiredMixin, UpdateView):
    model = User
    form_class = AdminUserUpdateForm
    template_name = "accounts/user_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        logger.debug("Starting UserUpdateView.get_form_kwargs")

        logger.debug(
            "Authenticated user: %s (ID: %s)",
            self.request.user.username,
            self.request.user.pk,
        )

        logger.debug(
            "Target user: %s (ID: %s)",
            self.object.username,
            self.object.pk,
        )

        kwargs["acting_user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "User updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("accounts:user_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit user"
        context["submit_label"] = "Save changes"
        context["cancel_url"] = reverse("accounts:user_list")
        context["target_user"] = self.object
        return context

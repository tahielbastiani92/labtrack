from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from apps.accounts.forms import LoginForm
from config.views import dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard, name="dashboard"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(authentication_form=LoginForm),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/users/", include("apps.accounts.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("api/v1/", include("config.api_urls")),
    path("projects/", include("apps.projects.urls")),
    path("samples/", include("apps.samples.urls")),
]

from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="list"),
    path("new/", views.ProjectCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.ProjectDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.ProjectUpdateView.as_view(), name="update"),
    path("<uuid:pk>/delete/", views.ProjectDeleteView.as_view(), name="delete"),
    path("<uuid:pk>/members/add/", views.membership_add, name="membership_add"),
    path(
        "<uuid:pk>/members/<uuid:membership_pk>/remove/",
        views.membership_remove,
        name="membership_remove",
    ),
]

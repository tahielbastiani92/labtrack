from django.urls import path

from . import views

app_name = "datasets"

urlpatterns = [
    path("", views.DatasetListView.as_view(), name="list"),
    path(
        "projects/<uuid:project_pk>/new/",
        views.DatasetCreateView.as_view(),
        name="create",
    ),
    path("<uuid:pk>/", views.DatasetDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.DatasetUpdateView.as_view(), name="update"),
    path("<uuid:pk>/delete/", views.DatasetDeleteView.as_view(), name="delete"),
]

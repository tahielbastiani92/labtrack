from django.urls import path

from . import views

app_name = "samples"

urlpatterns = [
    path("", views.SampleListView.as_view(), name="list"),
    path("projects/<uuid:project_pk>/new/", views.SampleCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.SampleDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.SampleUpdateView.as_view(), name="update"),
    path("<uuid:pk>/delete/", views.SampleDeleteView.as_view(), name="delete"),
]

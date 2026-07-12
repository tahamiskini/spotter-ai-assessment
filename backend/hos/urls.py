from django.urls import path

from . import views

urlpatterns = [
    path("healthcheck", views.healthcheck, name="healthcheck"),
    path("geocode", views.geocode_search, name="geocode-search"),
    path("trips/", views.TripCreateView.as_view(), name="create-trip"),
    path("trips/<uuid:trip_id>/", views.TripDetailView.as_view(), name="get-trip"),
]

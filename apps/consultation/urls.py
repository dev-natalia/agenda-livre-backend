from django.urls import path

from apps.consultation.views import (
    ActivityDetailView,
    ActivityListView,
    CategoryListView,
    UnitListView,
)

urlpatterns = [
    path("activities/", ActivityListView.as_view(), name="activity-list"),
    path("activities/<str:pk>/", ActivityDetailView.as_view(), name="activity-detail"),
    path("units/", UnitListView.as_view(), name="unit-list"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
]

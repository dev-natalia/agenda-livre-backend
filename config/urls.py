from django.contrib import admin
from django.urls import include, path, re_path

from apps.core.error_views import api_not_found

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/", include("apps.consultation.urls")),
    re_path(r"^api/", api_not_found),
]

handler404 = "apps.core.error_views.handler404"
handler500 = "apps.core.error_views.handler500"

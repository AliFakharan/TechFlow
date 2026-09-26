"""TechFlow URL configuration."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # OpenAPI schema + Swagger UI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/auth/", include("core.urls")),
    path("api/", include("organizations.urls")),
    path("api/", include("teams.urls")),
    path("api/", include("projects.urls")),
    path("api/", include("work.urls")),
    path("api/", include("blockers.urls")),
    path("api/", include("support.urls")),
    path("api/", include("capacity.urls")),
    path("api/", include("incoming.urls")),
    path("api/", include("audit_app.urls")),
    path("api/", include("dashboards.urls")),
]

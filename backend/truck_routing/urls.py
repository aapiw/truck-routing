import os
from pathlib import Path
from django.contrib import admin
from django.urls import path, re_path, include
from django.http import HttpResponse, FileResponse

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_INDEX = BASE_DIR.parent / "frontend" / "dist" / "index.html"


def serve_react_app(request):
    """Serves the built React index.html for root and client-side routing."""
    if FRONTEND_INDEX.exists():
        return FileResponse(open(FRONTEND_INDEX, "rb"))
    return HttpResponse(
        "<h1>TruckRoute Backend Active</h1><p>Frontend build (frontend/dist/index.html) not found. Run 'npm run build' inside frontend/.</p>",
        content_type="text/html",
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("routing_app.urls")),
    # Fallback to React app for all other URLs
    re_path(r"^(?!api/|admin/|static/).*$", serve_react_app),
]

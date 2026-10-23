from django.urls import path
from routing_app.views import HealthCheckView, GeocodeView, AnalyzeRoutesView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("geocode/", GeocodeView.as_view(), name="geocode"),
    path("routes/analyze/", AnalyzeRoutesView.as_view(), name="analyze_routes"),
]

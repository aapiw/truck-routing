import React, { useState, useEffect } from "react";
import Header from "./components/Header";
import RouteForm from "./components/RouteForm";
import RiskLegend from "./components/RiskLegend";
import RouteComparison from "./components/RouteComparison";
import MapView from "./components/MapView";
import TimelineSlider from "./components/TimelineSlider";
import CheckpointDetails from "./components/CheckpointDetails";
import { analyzeRoutes } from "./services/api";
import { AlertTriangle, Loader2 } from "lucide-react";
import "./App.css";

export default function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [selectedRouteId, setSelectedRouteId] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 0-48h forecast timeline state
  const [timelineHour, setTimelineHour] = useState(0);
  const [activeMetric, setActiveMetric] = useState("risk");

  // Initial load: automatically analyze Chicago to New York corridor
  useEffect(() => {
    const initialPayload = {
      origin: { lat: 41.8781, lon: -87.6298, label: "Chicago, IL" },
      destination: { lat: 40.7128, lon: -74.006, label: "New York, NY" },
      departure_time: new Date().toISOString(),
      load_weight: 42000,
      sampling_interval_miles: 25,
    };
    handleAnalyze(initialPayload);
  }, []);

  const handleAnalyze = async (payload) => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeRoutes(payload);
      setAnalysisResult(data);
      setSelectedRouteId(data.recommended_route_id ?? 0);
      setTimelineHour(0);
    } catch (err) {
      console.error("Error analyzing routes:", err);
      setError(err.message || "Failed to analyze routes. Please check connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const activeRoute = analysisResult?.routes?.find((r) => r.id === selectedRouteId) || analysisResult?.routes?.[0];

  return (
    <div className="app-layout">
      <Header />

      <main className="main-content">
        <div className="container">
          {/* Top Parameters & Legend */}
          <section className="form-section">
            <RouteForm onAnalyze={handleAnalyze} loading={loading} />
            <RiskLegend />
          </section>

          {/* Error Banner */}
          {error && (
            <div className="error-banner">
              <AlertTriangle size={18} className="mr-2 text-crimson flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Route Comparison Cards */}
          {analysisResult && (
            <RouteComparison
              routes={analysisResult.routes}
              selectedRouteId={selectedRouteId}
              onSelectRoute={setSelectedRouteId}
            />
          )}

          {/* Interactive Map & Timeline Section */}
          <section className="map-section card">
            <div className="map-section-header">
              <div>
                <h3 className="map-title">Route Corridor & Dynamic Weather Heatmap</h3>
                <span className="map-subtitle">
                  Visualizing {activeRoute?.name || "Active Route"} with ETA-based checkpoint weather & 0–48h forecast
                </span>
              </div>
            </div>

            <MapView
              routes={analysisResult?.routes || []}
              selectedRouteId={selectedRouteId}
              onSelectRoute={setSelectedRouteId}
              corridorGrid={analysisResult?.corridor_grid}
              timelineHour={timelineHour}
              activeMetric={activeMetric}
            />

            {/* 0-48 Hour Forecast Timeline Slider */}
            <TimelineSlider
              currentHour={timelineHour}
              maxHours={48}
              timestamps={analysisResult?.corridor_grid?.timestamps || []}
              onChangeHour={setTimelineHour}
              activeMetric={activeMetric}
              onChangeMetric={setActiveMetric}
            />
          </section>

          {/* Checkpoint Audit Log */}
          {activeRoute && (
            <section className="audit-section">
              <CheckpointDetails
                checkpoints={activeRoute.checkpoints || []}
                routeName={activeRoute.name}
              />
            </section>
          )}
        </div>
      </main>

      <footer className="app-footer">
        <div className="container footer-content">
          <span>TruckRoute Safety Engine &copy; {new Date().getFullYear()}</span>
          <span>Open-Meteo Meteorological Service &bull; OSRM Engine &bull; Compliant with DOT & OSHA Safety Rules</span>
        </div>
      </footer>
    </div>
  );
}

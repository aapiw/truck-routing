import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Ensure L is on window for leaflet plugins if needed
if (typeof window !== "undefined") {
  window.L = L;
}
import { Layers, Eye, EyeOff, Maximize2, Wind, CloudRain, Snowflake, Thermometer, ShieldAlert } from "lucide-react";
import { RISK_COLORS, RISK_LABELS } from "../utils/formatters";

export default function MapView({
  routes = [],
  selectedRouteId = 0,
  onSelectRoute,
  corridorGrid = null,
  timelineHour = 0,
  activeMetric = "risk",
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);

  // Layer groups
  const activeRouteLayerRef = useRef(L.layerGroup());
  const inactiveRoutesLayerRef = useRef(L.layerGroup());
  const checkpointsLayerRef = useRef(L.layerGroup());
  const heatmapLayerRef = useRef(L.layerGroup());

  // Layer visibility toggles
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showOtherRoutes, setShowOtherRoutes] = useState(true);
  const [showCheckpoints, setShowCheckpoints] = useState(true);

  // Initialize Map Once
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [39.8283, -98.5795], // Geographic center of US
      zoom: 5,
      zoomControl: true,
      preferCanvas: true,
    });

    // Stadia Maps (alidade_smooth) - OSM-based, policy-compliant, free API key
    const stadiaApiKey = import.meta.env.VITE_STADIA_API_KEY;
    L.tileLayer(
      `https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png?api_key=${stadiaApiKey}`,
      {
        maxZoom: 20,
        attribution:
          '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> ' +
          '&copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> ' +
          '&copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
      }
    ).addTo(map);

    // Add layer groups to map
    heatmapLayerRef.current.addTo(map);
    inactiveRoutesLayerRef.current.addTo(map);
    activeRouteLayerRef.current.addTo(map);
    checkpointsLayerRef.current.addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Routes & Fit Bounds
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !routes || routes.length === 0) return;

    activeRouteLayerRef.current.clearLayers();
    inactiveRoutesLayerRef.current.clearLayers();
    checkpointsLayerRef.current.clearLayers();

    const selectedRoute = routes.find((r) => r.id === selectedRouteId) || routes[0];

    // 1. Draw Inactive Routes
    if (showOtherRoutes) {
      routes.forEach((r) => {
        if (r.id !== selectedRoute.id && r.coordinates && r.coordinates.length > 0) {
          const polyline = L.polyline(r.coordinates, {
            color: "#64748b",
            weight: 3.5,
            opacity: 0.55,
            dashArray: "6, 8",
          });
          polyline.bindTooltip(`${r.name} (${r.duration_formatted})`, { sticky: true });
          polyline.on("click", () => onSelectRoute(r.id));
          inactiveRoutesLayerRef.current.addLayer(polyline);
        }
      });
    }

    // 2. Draw Active Route with Risk-Colored Segments
    if (selectedRoute.colored_segments && selectedRoute.colored_segments.length > 0) {
      selectedRoute.colored_segments.forEach((seg) => {
        const poly = L.polyline(seg.coordinates, {
          color: seg.color || "#10b981",
          weight: 6.5,
          opacity: 0.95,
          lineJoin: "round",
          lineCap: "round",
        });
        activeRouteLayerRef.current.addLayer(poly);
      });
    } else if (selectedRoute.coordinates && selectedRoute.coordinates.length > 0) {
      const poly = L.polyline(selectedRoute.coordinates, {
        color: "#2563eb",
        weight: 6,
        opacity: 0.9,
      });
      activeRouteLayerRef.current.addLayer(poly);
    }

    // 3. Draw Checkpoints on Active Route
    if (showCheckpoints && selectedRoute.checkpoints) {
      selectedRoute.checkpoints.forEach((cp, idx) => {
        const isOrigin = cp.is_origin;
        const isDest = cp.is_destination;
        const riskLevel = cp.risk?.overall_risk || "LOW";
        const pinColor = RISK_COLORS[riskLevel] || "#10b981";

        let marker;
        if (isOrigin || isDest) {
          marker = L.circleMarker([cp.lat, cp.lon], {
            radius: 11,
            fillColor: isOrigin ? "#10b981" : "#ef4444",
            color: "#ffffff",
            weight: 3,
            fillOpacity: 1.0,
          });
        } else {
          marker = L.circleMarker([cp.lat, cp.lon], {
            radius: 6.5,
            fillColor: pinColor,
            color: "#ffffff",
            weight: 2,
            fillOpacity: 0.95,
          });
        }

        // Popup Content
        const w = cp.weather || {};
        const popupContent = `
          <div class="map-popup">
            <div class="popup-header">
              <strong>${isOrigin ? "Origin" : isDest ? "Destination" : `Checkpoint #${idx}`}</strong>
              <span class="popup-eta">${cp.eta_formatted || "ETA"}</span>
            </div>
            <div class="popup-distance">${cp.distance_from_origin_miles} mi from origin</div>
            
            <div class="popup-risk-badge" style="background-color: ${pinColor}; color: #ffffff;">
              ${RISK_LABELS[riskLevel] || riskLevel}
            </div>

            <div class="popup-weather-grid">
              <div class="weather-row">
                <span>Wind:</span>
                <strong>${w.wind_speed_mph || 0} mph (gusts ${w.wind_gusts_mph || 0})</strong>
              </div>
              <div class="weather-row">
                <span>Rain:</span>
                <strong>${w.rain_in_per_hr || 0} in/hr</strong>
              </div>
              <div class="weather-row">
                <span>Snow:</span>
                <strong>${w.snow_in_per_hr || 0} in/hr</strong>
              </div>
              <div class="weather-row">
                <span>Temp:</span>
                <strong>${w.temperature_f || 60}°F (${w.description || "Clear"})</strong>
              </div>
            </div>

            ${
              cp.risk?.load_rule_note
                ? `<div class="popup-load-alert">
                    <span class="load-alert-title">⚠ Weight Rule Escalation:</span>
                    <span>${cp.risk.load_rule_note}</span>
                  </div>`
                : ""
            }
          </div>
        `;

        marker.bindPopup(popupContent, { maxWidth: 280, className: "custom-leaflet-popup" });
        checkpointsLayerRef.current.addLayer(marker);
      });
    }

    // 4. Fit bounds to active route coordinates
    if (selectedRoute.coordinates && selectedRoute.coordinates.length > 0) {
      const bounds = L.latLngBounds(selectedRoute.coordinates);
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
    }
  }, [routes, selectedRouteId, showOtherRoutes, showCheckpoints, onSelectRoute]);

  // Update Weather Heatmap on Corridor
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !corridorGrid || !corridorGrid.grid) return;

    heatmapLayerRef.current.clearLayers();
    if (!showHeatmap) return;

    const pts = corridorGrid.grid;
    pts.forEach((pt) => {
      const hourlyData = pt.hourly && pt.hourly[timelineHour] ? pt.hourly[timelineHour] : null;
      if (!hourlyData) return;

      let intensity = 0.1;
      let color = "#3b82f6";

      if (activeMetric === "wind") {
        const speed = hourlyData.wind_mph || 0;
        intensity = Math.min(1.0, speed / 55.0);
        if (speed >= 55) color = "#7f1d1d";
        else if (speed >= 45) color = "#ef4444";
        else if (speed >= 35) color = "#f97316";
        else if (speed >= 25) color = "#f59e0b";
        else color = "#10b981";
      } else if (activeMetric === "rain") {
        const rain = hourlyData.rain_in || 0;
        intensity = Math.min(1.0, rain / 1.0);
        if (rain > 1.0) color = "#7f1d1d";
        else if (rain >= 0.5) color = "#ef4444";
        else if (rain >= 0.25) color = "#f97316";
        else if (rain >= 0.1) color = "#3b82f6";
        else color = "#93c5fd";
      } else if (activeMetric === "snow") {
        const snow = hourlyData.snow_in || 0;
        intensity = Math.min(1.0, snow / 3.0);
        if (snow > 3.0) color = "#7f1d1d";
        else if (snow >= 2.0) color = "#ef4444";
        else if (snow >= 1.0) color = "#c084fc";
        else if (snow >= 0.5) color = "#a855f7";
        else color = "#e2e8f0";
      } else {
        // Composite Risk
        intensity = hourlyData.risk_intensity || 0.1;
        if (intensity >= 0.8) color = "#ef4444";
        else if (intensity >= 0.5) color = "#f97316";
        else if (intensity >= 0.3) color = "#f59e0b";
        else color = "#10b981";
      }

      if (intensity > 0.05) {
        const radiusMeters = 24000;
        const circle = L.circle([pt.lat, pt.lon], {
          radius: radiusMeters,
          fillColor: color,
          fillOpacity: Math.max(0.12, Math.min(0.55, intensity * 0.6)),
          stroke: false,
        });
        heatmapLayerRef.current.addLayer(circle);
      }
    });
  }, [corridorGrid, timelineHour, activeMetric, showHeatmap]);

  const fitBounds = () => {
    const map = mapInstanceRef.current;
    if (!map || !routes || routes.length === 0) return;
    const selectedRoute = routes.find((r) => r.id === selectedRouteId) || routes[0];
    if (selectedRoute.coordinates && selectedRoute.coordinates.length > 0) {
      map.fitBounds(L.latLngBounds(selectedRoute.coordinates), { padding: [50, 50] });
    }
  };

  return (
    <div className="map-view-container">
      <div className="map-controls-overlay">
        <div className="map-toggles-card">
          <button
            type="button"
            className={`btn-map-toggle ${showHeatmap ? "active" : ""}`}
            onClick={() => setShowHeatmap(!showHeatmap)}
            title="Toggle Corridor Weather Heatmap"
          >
            <Layers size={14} className="mr-1" />
            Heatmap
          </button>

          <button
            type="button"
            className={`btn-map-toggle ${showCheckpoints ? "active" : ""}`}
            onClick={() => setShowCheckpoints(!showCheckpoints)}
            title="Toggle Checkpoint Markers"
          >
            {showCheckpoints ? <Eye size={14} className="mr-1" /> : <EyeOff size={14} className="mr-1" />}
            Checkpoints
          </button>

          <button
            type="button"
            className={`btn-map-toggle ${showOtherRoutes ? "active" : ""}`}
            onClick={() => setShowOtherRoutes(!showOtherRoutes)}
            title="Toggle Alternate Route Options"
          >
            Alternate Routes
          </button>

          <button type="button" className="btn-map-toggle" onClick={fitBounds} title="Recenter Route Corridor">
            <Maximize2 size={14} />
          </button>
        </div>
      </div>

      <div ref={mapContainerRef} className="leaflet-map-element" />
    </div>
  );
}

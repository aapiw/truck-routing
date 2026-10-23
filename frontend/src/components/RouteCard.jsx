import React from "react";
import { CheckCircle, AlertTriangle, Clock, Route as RouteIcon, ShieldAlert, Award, FlaskConical } from "lucide-react";
import { RISK_COLORS } from "../utils/formatters";

export default function RouteCard({ route, isSelected, onSelect }) {
  const stats = route.risk_summary || {};
  const isRecommended = route.is_recommended;
  const isDemo = route.demo_risk_level;
  const totMiles = stats.total_miles || route.distance_miles || 1;

  // Percentages for stacked risk bar
  const pLow = ((stats.low_miles || 0) / totMiles) * 100;
  const pMod = ((stats.moderate_miles || 0) / totMiles) * 100;
  const pHigh = ((stats.high_miles || 0) / totMiles) * 100;
  const pSev = ((stats.severe_miles || 0) / totMiles) * 100;
  const pNoTrav = ((stats.no_travel_miles || 0) / totMiles) * 100;

  const criticalSevereMiles = (stats.severe_miles || 0) + (stats.no_travel_miles || 0);

  return (
    <div
      className={`card route-card ${isSelected ? "route-card-selected" : ""} ${isRecommended ? "route-card-recommended" : ""}`}
      onClick={() => onSelect(route.id)}
    >
<div className="card-top-banner">
        <div className="route-header-info">
          <div className="route-title-row">
            <h3 className="route-name">{route.name}</h3>
            {isDemo && (
              <span className="badge demo-badge" style={{ backgroundColor: RISK_COLORS[route.demo_risk_level] + "20", color: RISK_COLORS[route.demo_risk_level], borderColor: RISK_COLORS[route.demo_risk_level] }}>
                <FlaskConical size={12} className="mr-1" />
                Demo: {route.demo_risk_level}
              </span>
            )}
            {isRecommended ? (
              <span className="badge badge-recommended">
                <Award size={14} className="mr-1" />
                Recommended
              </span>
            ) : (
              <span className="badge badge-rank">Option #{route.rank}</span>
            )}
          </div>
          <span className="route-summary">{route.summary || "Standard Corridor"}</span>
        </div>
      </div>

      {/* Stacked Risk Mileage Bar */}
      <div className="risk-bar-container">
        <div className="risk-bar-label-row">
          <span className="risk-bar-title">Corridor Risk Breakdown</span>
          <span className="risk-bar-total">{totMiles.toFixed(0)} mi total</span>
        </div>
        <div className="stacked-risk-bar">
          {pLow > 0 && (
            <div
              className="risk-bar-slice"
              style={{ width: `${pLow}%`, backgroundColor: RISK_COLORS.LOW }}
              title={`Low: ${stats.low_miles} mi (${pLow.toFixed(0)}%)`}
            />
          )}
          {pMod > 0 && (
            <div
              className="risk-bar-slice"
              style={{ width: `${pMod}%`, backgroundColor: RISK_COLORS.MODERATE }}
              title={`Moderate: ${stats.moderate_miles} mi (${pMod.toFixed(0)}%)`}
            />
          )}
          {pHigh > 0 && (
            <div
              className="risk-bar-slice"
              style={{ width: `${pHigh}%`, backgroundColor: RISK_COLORS.HIGH }}
              title={`High: ${stats.high_miles} mi (${pHigh.toFixed(0)}%)`}
            />
          )}
          {pSev > 0 && (
            <div
              className="risk-bar-slice"
              style={{ width: `${pSev}%`, backgroundColor: RISK_COLORS.SEVERE }}
              title={`Severe: ${stats.severe_miles} mi (${pSev.toFixed(0)}%)`}
            />
          )}
          {pNoTrav > 0 && (
            <div
              className="risk-bar-slice"
              style={{ width: `${pNoTrav}%`, backgroundColor: RISK_COLORS.NO_TRAVEL }}
              title={`No Travel: ${stats.no_travel_miles} mi (${pNoTrav.toFixed(0)}%)`}
            />
          )}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="route-metrics-grid">
        <div className="metric-box">
          <div className="metric-icon-label">
            <Clock size={14} className="text-muted" />
            <span>Travel Time</span>
          </div>
          <span className="metric-value">{route.duration_formatted}</span>
        </div>

        <div className="metric-box">
          <div className="metric-icon-label">
            <RouteIcon size={14} className="text-muted" />
            <span>Distance</span>
          </div>
          <span className="metric-value">{route.distance_miles} mi</span>
        </div>

        <div className="metric-box">
          <div className="metric-icon-label">
            <ShieldAlert size={14} className={criticalSevereMiles > 0 ? "text-crimson" : "text-emerald"} />
            <span>Severe Miles</span>
          </div>
          <span className={`metric-value ${criticalSevereMiles > 0 ? "text-crimson" : "text-emerald"}`}>
            {criticalSevereMiles.toFixed(1)} mi
          </span>
        </div>

        <div className="metric-box">
          <div className="metric-icon-label">
            <AlertTriangle size={14} className={stats.high_miles > 0 ? "text-amber" : "text-emerald"} />
            <span>High Miles</span>
          </div>
          <span className="metric-value">{(stats.high_miles || 0).toFixed(1)} mi</span>
        </div>
      </div>

      {/* Recommendation Rationale */}
      <div className={`recommendation-note ${isRecommended ? "note-recommended" : "note-secondary"}`}>
        <p className="note-text">{route.recommendation_reason}</p>
      </div>

      {/* Load rule escalation warnings */}
      {stats.load_alerts && stats.load_alerts.length > 0 && (
        <div className="load-alert-tag">
          <AlertTriangle size={13} className="text-crimson mr-1" />
          <span>{stats.load_alerts.length} checkpoint(s) escalated by load weight rule</span>
        </div>
      )}

      <button
        type="button"
        className={`btn-select-route ${isSelected ? "btn-selected" : ""}`}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(route.id);
        }}
      >
        {isSelected ? "Active on Map" : "Select Route"}
      </button>
    </div>
  );
}

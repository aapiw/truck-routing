import React, { useState } from "react";
import { AlertCircle, Filter, ChevronRight, Wind, CloudRain, Snowflake, Clock } from "lucide-react";
import { RISK_COLORS, RISK_LABELS } from "../utils/formatters";

export default function CheckpointDetails({ checkpoints = [], routeName = "" }) {
  const [filter, setFilter] = useState("ALL"); // ALL, HAZARDS (High/Severe/NoTravel), MOD_PLUS

  if (!checkpoints || checkpoints.length === 0) return null;

  const filtered = checkpoints.filter((cp) => {
    const lvl = cp.risk?.overall_risk || "LOW";
    if (filter === "HAZARDS") {
      return lvl === "HIGH" || lvl === "SEVERE" || lvl === "NO_TRAVEL";
    }
    if (filter === "MOD_PLUS") {
      return lvl !== "LOW";
    }
    return true;
  });

  return (
    <div className="card checkpoint-log-card">
      <div className="log-header">
        <div className="log-title-area">
          <h3 className="log-title">Route Checkpoint Weather Audit</h3>
          <span className="log-subtitle">
            {checkpoints.length} checkpoints sampled along {routeName}
          </span>
        </div>

        <div className="filter-pill-group">
          <button
            type="button"
            className={`filter-pill ${filter === "ALL" ? "active" : ""}`}
            onClick={() => setFilter("ALL")}
          >
            All ({checkpoints.length})
          </button>
          <button
            type="button"
            className={`filter-pill ${filter === "MOD_PLUS" ? "active" : ""}`}
            onClick={() => setFilter("MOD_PLUS")}
          >
            Moderate+
          </button>
          <button
            type="button"
            className={`filter-pill ${filter === "HAZARDS" ? "active" : ""}`}
            onClick={() => setFilter("HAZARDS")}
          >
            Hazards Only
          </button>
        </div>
      </div>

      <div className="table-responsive log-table-wrapper">
        <table className="checkpoint-table">
          <thead>
            <tr>
              <th>Mile / Landmark</th>
              <th>Truck ETA</th>
              <th>Wind</th>
              <th>Rain</th>
              <th>Snow</th>
              <th>Temp / Condition</th>
              <th>Risk Assessment</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan="7" className="text-center py-4 text-muted">
                  No checkpoints match the selected filter.
                </td>
              </tr>
            ) : (
              filtered.map((cp) => {
                const w = cp.weather || {};
                const r = cp.risk || {};
                const lvl = r.overall_risk || "LOW";
                const color = RISK_COLORS[lvl] || "#10b981";

                return (
                  <tr key={cp.index} className={r.load_rule_note ? "row-escalated" : ""}>
                    <td className="font-medium">
                      {cp.is_origin ? (
                        <span className="text-emerald font-semibold">Origin (0.0 mi)</span>
                      ) : cp.is_destination ? (
                        <span className="text-crimson font-semibold">Destination ({cp.distance_from_origin_miles} mi)</span>
                      ) : (
                        `Mi ${cp.distance_from_origin_miles}`
                      )}
                    </td>
                    <td>
                      <div className="eta-cell">
                        <Clock size={13} className="text-muted mr-1 inline" />
                        <span>{cp.eta_formatted}</span>
                      </div>
                    </td>
                    <td>
                      <span className={w.wind_speed_mph >= 35 ? "text-danger font-semibold" : ""}>
                        {w.wind_speed_mph} mph
                      </span>
                      {w.wind_gusts_mph > w.wind_speed_mph && (
                        <span className="text-xs text-muted block">gusts {w.wind_gusts_mph}</span>
                      )}
                    </td>
                    <td>
                      <span className={w.rain_in_per_hr >= 0.25 ? "text-danger font-semibold" : ""}>
                        {w.rain_in_per_hr} in/hr
                      </span>
                    </td>
                    <td>
                      <span className={w.snow_in_per_hr >= 1.0 ? "text-danger font-semibold" : ""}>
                        {w.snow_in_per_hr} in/hr
                      </span>
                    </td>
                    <td>
                      <span>{w.temperature_f}°F</span>
                      <span className="text-xs text-muted block">{w.description}</span>
                    </td>
                    <td>
                      <span
                        className="checkpoint-risk-pill"
                        style={{ backgroundColor: color, color: "#ffffff" }}
                      >
                        {RISK_LABELS[lvl] || lvl}
                      </span>
                      {r.load_rule_note && (
                        <div className="escalation-tooltip" title={r.load_rule_note}>
                          ⚠ {r.load_rule_note}
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

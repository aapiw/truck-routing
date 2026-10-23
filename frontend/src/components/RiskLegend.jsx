import React, { useState } from "react";
import { Info, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import { RISK_COLORS } from "../utils/formatters";

export default function RiskLegend() {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card legend-card">
      <div className="legend-header" onClick={() => setExpanded(!expanded)}>
        <div className="legend-title">
          <Info size={16} className="text-blue" />
          <span>Weather Risk Rules & Load Weight Protocols</span>
        </div>
        <div className="legend-items-inline">
          <span className="legend-badge" style={{ backgroundColor: RISK_COLORS.LOW }}>Low</span>
          <span className="legend-badge" style={{ backgroundColor: RISK_COLORS.MODERATE }}>Moderate</span>
          <span className="legend-badge" style={{ backgroundColor: RISK_COLORS.HIGH }}>High</span>
          <span className="legend-badge" style={{ backgroundColor: RISK_COLORS.SEVERE }}>Severe</span>
          <span className="legend-badge text-white" style={{ backgroundColor: RISK_COLORS.NO_TRAVEL }}>No Travel</span>
        </div>
        <button type="button" className="btn-toggle-legend">
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {expanded && (
        <div className="legend-body">
          <div className="table-responsive">
            <table className="rules-table">
              <thead>
                <tr>
                  <th>Condition</th>
                  <th>Low</th>
                  <th>Moderate</th>
                  <th>High</th>
                  <th>Severe</th>
                  <th>No Travel</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="font-semibold">Wind</td>
                  <td>&lt; 25 mph</td>
                  <td>25–34 mph</td>
                  <td>35–44 mph</td>
                  <td>45–54 mph</td>
                  <td>≥ 55 mph</td>
                </tr>
                <tr>
                  <td className="font-semibold">Rain</td>
                  <td>&lt; 0.10 in/hr</td>
                  <td>0.10–0.25</td>
                  <td>0.25–0.50</td>
                  <td>0.50–1.00</td>
                  <td>&gt; 1.00 in/hr</td>
                </tr>
                <tr>
                  <td className="font-semibold">Snow</td>
                  <td>&lt; 0.5 in/hr</td>
                  <td>0.5–1.0</td>
                  <td>1.0–2.0</td>
                  <td>2.0–3.0</td>
                  <td>&gt; 3.0 in/hr</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="load-rules-box">
            <div className="load-rules-title">
              <AlertTriangle size={15} className="text-amber" />
              <span>Mandatory Load Weight Escalation Rules</span>
            </div>
            <ul className="load-rules-list">
              <li>
                <strong>≥ 55 mph Wind:</strong> Immediate <strong>No Travel</strong> advisory for any truck/load weight.
              </li>
              <li>
                <strong>45–54 mph Wind + &gt; 30,000 lb Load:</strong> Escalated to <strong>No Travel</strong> (high rollover hazard).
              </li>
              <li>
                <strong>35–44 mph Wind + &gt; 40,000 lb Load:</strong> Escalated to <strong>Severe Risk</strong> (crosswind instability).
              </li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

import React from "react";
import RouteCard from "./RouteCard";
import { CheckCircle2, ShieldCheck, TrendingDown } from "lucide-react";

export default function RouteComparison({ routes, selectedRouteId, onSelectRoute }) {
  if (!routes || routes.length === 0) return null;

  const recommended = routes.find((r) => r.is_recommended) || routes[0];

  return (
    <section className="route-comparison-section">
      <div className="section-header">
        <div>
          <h2 className="section-title">3 Route Options Evaluated</h2>
          <p className="section-subtitle">
            Ranked by fewest severe miles, fewest high miles, lowest average risk, and travel time
          </p>
        </div>

        {recommended && (
          <div className="recommended-callout">
            <ShieldCheck size={18} className="text-emerald mr-2" />
            <span>
              Optimal Choice: <strong>{recommended.name}</strong> ({recommended.duration_formatted})
            </span>
          </div>
        )}
      </div>

      <div className="routes-grid">
        {routes.map((route) => (
          <RouteCard
            key={route.id}
            route={route}
            isSelected={route.id === selectedRouteId}
            onSelect={onSelectRoute}
          />
        ))}
      </div>
    </section>
  );
}

import React from "react";
import { Truck, ShieldCheck, CloudRain, Navigation } from "lucide-react";

export default function Header() {
  return (
    <header className="app-header">
      <div className="header-container">
        <div className="brand">

          <div className="brand-text">
            <h1 className="brand-title">TruckRoute</h1>
            <span className="brand-subtitle">Weather-Aware Truck Routing</span>
          </div>
        </div>

        <div className="header-meta">


        </div>
      </div>
    </header>
  );
}

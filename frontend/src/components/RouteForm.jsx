import React, { useState, useEffect, useRef } from "react";
import { MapPin, Navigation, Calendar, Scale, Gauge, Search, Loader2 } from "lucide-react";
import { searchGeocode } from "../services/api";

const PRESET_ROUTES = [
  {
    name: "Chicago → New York",
    origin: { lat: 41.8781, lon: -87.6298, label: "Chicago, IL" },
    destination: { lat: 40.7128, lon: -74.006, label: "New York, NY" },
  },
  {
    name: "Denver → Salt Lake City",
    origin: { lat: 39.7392, lon: -104.9903, label: "Denver, CO" },
    destination: { lat: 40.7608, lon: -111.891, label: "Salt Lake City, UT" },
  },
  {
    name: "Seattle → Portland",
    origin: { lat: 47.6062, lon: -122.3321, label: "Seattle, WA" },
    destination: { lat: 45.5152, lon: -122.6784, label: "Portland, OR" },
  },
  {
    name: "Dallas → Atlanta",
    origin: { lat: 32.7767, lon: -96.797, label: "Dallas, TX" },
    destination: { lat: 33.749, lon: -84.388, label: "Atlanta, GA" },
  },
  {
    name: "I-80 Wyoming (High Wind Corridor)",
    origin: { lat: 41.14, lon: -104.82, label: "Cheyenne, WY" },
    destination: { lat: 41.79, lon: -109.24, label: "Rock Springs, WY" },
  },
  {
    name: "I-70 Colorado Mountains (Vail Pass)",
    origin: { lat: 39.74, lon: -105.27, label: "Idaho Springs, CO" },
    destination: { lat: 39.64, lon: -106.37, label: "Vail, CO" },
  },
  {
    name: "Tornado Alley (OKC → Amarillo)",
    origin: { lat: 35.47, lon: -97.52, label: "Oklahoma City, OK" },
    destination: { lat: 35.22, lon: -101.83, label: "Amarillo, TX" },
  },
  {
    name: "Sierra Nevada (Donner Pass)",
    origin: { lat: 39.33, lon: -120.19, label: "Truckee, CA" },
    destination: { lat: 39.16, lon: -119.77, label: "Reno, NV" },
  },
  // Risk-level demonstration presets (weather-dependent):
  {
    name: "⬤ LOW — Phoenix → San Diego (Clear Desert)",
    origin: { lat: 33.4484, lon: -112.074, label: "Phoenix, AZ" },
    destination: { lat: 32.7157, lon: -117.1611, label: "San Diego, CA" },
    demo_risk_level: "LOW",
  },
  {
    name: "⬤ MODERATE — Portland → Eugene (Pacific NW Rain)",
    origin: { lat: 45.5152, lon: -122.6784, label: "Portland, OR" },
    destination: { lat: 44.0521, lon: -123.0868, label: "Eugene, OR" },
    demo_risk_level: "MODERATE",
  },
  {
    name: "⬤ HIGH — I-80 Donner Summit (Sierra Wind/Snow)",
    origin: { lat: 39.32, lon: -120.33, label: "Soda Springs, CA" },
    destination: { lat: 39.31, lon: -119.77, label: "Reno, NV" },
    demo_risk_level: "HIGH",
  },
  {
    name: "⬤ SEVERE — I-70 Eisenhower Tunnel (CO Alpine)",
    origin: { lat: 39.67, lon: -105.85, label: "Silverthorne, CO" },
    destination: { lat: 39.74, lon: -105.93, label: "Georgetown, CO" },
    demo_risk_level: "SEVERE",
  },
  {
    name: "⬤ NO TRAVEL — OK Panhandle Spring (Tornado Alley Core)",
    origin: { lat: 36.92, lon: -101.48, label: "Boise City, OK" },
    destination: { lat: 36.31, lon: -100.14, label: "Perryton, TX" },
    demo_risk_level: "NO_TRAVEL",
  },
];

const WEIGHT_PRESETS = [
  { label: "Empty (15k lb)", weight: 15000 },
  { label: "Standard (32k lb)", weight: 32000 },
  { label: "Heavy (>40k lb)", weight: 42000 },
  { label: "Max (>50k lb)", weight: 52000 },
];

export default function RouteForm({ onAnalyze, loading }) {
  const [origin, setOrigin] = useState(PRESET_ROUTES[0].origin);
  const [destination, setDestination] = useState(PRESET_ROUTES[0].destination);

  const [originQuery, setOriginQuery] = useState(PRESET_ROUTES[0].origin.label);
  const [destQuery, setDestQuery] = useState(PRESET_ROUTES[0].destination.label);

  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destSuggestions, setDestSuggestions] = useState([]);

  const [isSearchingOrigin, setIsSearchingOrigin] = useState(false);
  const [isSearchingDest, setIsSearchingDest] = useState(false);

  const [departureTime, setDepartureTime] = useState(() => {
    const now = new Date();
    // Default to top of the next hour
    now.setHours(now.getHours() + 1, 0, 0, 0);
    return now.toISOString().slice(0, 16);
  });

  const [loadWeight, setLoadWeight] = useState(42000);
  const [samplingInterval, setSamplingInterval] = useState(25);
  const [selectedPreset, setSelectedPreset] = useState(null);

  const originDebounceRef = useRef(null);
  const destDebounceRef = useRef(null);

  const handleOriginChange = (e) => {
    const val = e.target.value;
    setOriginQuery(val);
    clearTimeout(originDebounceRef.current);
    if (val.trim().length >= 2) {
      setIsSearchingOrigin(true);
      originDebounceRef.current = setTimeout(async () => {
        const res = await searchGeocode(val);
        setOriginSuggestions(res);
        setIsSearchingOrigin(false);
      }, 350);
    } else {
      setOriginSuggestions([]);
      setIsSearchingOrigin(false);
    }
  };

  const handleDestChange = (e) => {
    const val = e.target.value;
    setDestQuery(val);
    clearTimeout(destDebounceRef.current);
    if (val.trim().length >= 2) {
      setIsSearchingDest(true);
      destDebounceRef.current = setTimeout(async () => {
        const res = await searchGeocode(val);
        setDestSuggestions(res);
        setIsSearchingDest(false);
      }, 350);
    } else {
      setDestSuggestions([]);
      setIsSearchingDest(false);
    }
  };

  const selectOrigin = (item) => {
    setOrigin(item);
    setOriginQuery(item.label);
    setOriginSuggestions([]);
  };

  const selectDest = (item) => {
    setDestination(item);
    setDestQuery(item.label);
    setDestSuggestions([]);
  };

  const applyPreset = (preset) => {
    setOrigin(preset.origin);
    setOriginQuery(preset.origin.label);
    setDestination(preset.destination);
    setDestQuery(preset.destination.label);
    setOriginSuggestions([]);
    setDestSuggestions([]);
    setSelectedPreset(preset);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!origin || !destination) return;

    const payload = {
      origin,
      destination,
      departure_time: new Date(departureTime).toISOString(),
      load_weight: Number(loadWeight),
      sampling_interval_miles: Number(samplingInterval),
    };

    // Enable demo mode for presets that specify a demo risk level
    if (selectedPreset?.demo_risk_level) {
      payload.demo_mode = false;
    }

    onAnalyze(payload);
  };

  return (
    <div className="card form-card">
      <div className="presets-bar">
        <span className="presets-label">Corridor Presets:</span>
        <div className="presets-buttons">
          {PRESET_ROUTES.map((p, idx) => (
            <button
              key={idx}
              type="button"
              className={`btn-preset ${originQuery === p.origin.label ? "active" : ""}`}
              onClick={() => applyPreset(p)}
            >
              {p.name}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="route-form">
        <div className="form-grid">
          {/* Origin Input */}
          <div className="input-group relative">
            <label className="input-label">
              <MapPin size={15} className="text-emerald" />
              <span>Origin</span>
            </label>
            <div className="input-wrapper">
              <input
                type="text"
                className="text-input"
                value={originQuery}
                onChange={handleOriginChange}
                placeholder="City, state, or address..."
                required
              />
              {isSearchingOrigin && <Loader2 size={16} className="input-spinner" />}
            </div>

            {originSuggestions.length > 0 && (
              <ul className="dropdown-suggestions">
                {originSuggestions.map((item, idx) => (
                  <li key={idx} onClick={() => selectOrigin(item)}>
                    <MapPin size={14} className="text-muted" />
                    <span>{item.label}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Destination Input */}
          <div className="input-group relative">
            <label className="input-label">
              <Navigation size={15} className="text-crimson" />
              <span>Destination</span>
            </label>
            <div className="input-wrapper">
              <input
                type="text"
                className="text-input"
                value={destQuery}
                onChange={handleDestChange}
                placeholder="City, state, or address..."
                required
              />
              {isSearchingDest && <Loader2 size={16} className="input-spinner" />}
            </div>

            {destSuggestions.length > 0 && (
              <ul className="dropdown-suggestions">
                {destSuggestions.map((item, idx) => (
                  <li key={idx} onClick={() => selectDest(item)}>
                    <Navigation size={14} className="text-muted" />
                    <span>{item.label}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Departure Date/Time */}
          <div className="input-group">
            <label className="input-label">
              <Calendar size={15} className="text-blue" />
              <span>Departure Time</span>
            </label>
            <input
              type="datetime-local"
              className="text-input"
              value={departureTime}
              onChange={(e) => setDepartureTime(e.target.value)}
              required
            />
          </div>

          {/* Load Weight */}
          <div className="input-group">
            <label className="input-label">
              <Scale size={15} className="text-amber" />
              <span>Load Weight (lbs)</span>
            </label>
            <input
              type="number"
              className="text-input"
              value={loadWeight}
              onChange={(e) => setLoadWeight(Math.max(0, Number(e.target.value)))}
              step="500"
              min="0"
              max="100000"
              required
            />
            <div className="weight-chips">
              {WEIGHT_PRESETS.map((wp, idx) => (
                <button
                  key={idx}
                  type="button"
                  className={`chip ${loadWeight === wp.weight ? "chip-active" : ""}`}
                  onClick={() => setLoadWeight(wp.weight)}
                >
                  {wp.label}
                </button>
              ))}
            </div>
          </div>

          {/* Sampling Interval */}
          <div className="input-group">
            <label className="input-label">
              <Gauge size={15} className="text-purple" />
              <span>Sampling Resolution</span>
            </label>
            <div className="interval-toggle-group">
              {[10, 25, 50].map((interval) => (
                <button
                  key={interval}
                  type="button"
                  className={`btn-interval ${samplingInterval === interval ? "active" : ""}`}
                  onClick={() => setSamplingInterval(interval)}
                >
                  Every {interval} mi
                </button>
              ))}
            </div>
            <span className="input-hint">Samples weather at arrival ETA along corridor</span>
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin mr-2" />
                Analyzing 3 Routes & Dynamic Weather...
              </>
            ) : (
              <>
                <Search size={18} className="mr-2" />
                Analyze Routes & Evaluate Risk
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

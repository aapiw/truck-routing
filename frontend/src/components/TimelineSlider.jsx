import React, { useEffect, useState, useRef } from "react";
import { Play, Pause, RotateCcw, FastForward, Wind, CloudRain, Snowflake, AlertCircle } from "lucide-react";

export default function TimelineSlider({
  currentHour,
  maxHours = 48,
  timestamps = [],
  onChangeHour,
  activeMetric,
  onChangeMetric,
}) {
  const [isPlaying, setIsPlaying] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        onChangeHour((prev) => {
          if (prev >= maxHours) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 500);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [isPlaying, maxHours, onChangeHour]);

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const resetTimeline = () => {
    setIsPlaying(false);
    onChangeHour(0);
  };

  const currentTimestampStr = timestamps[currentHour]
    ? new Date(timestamps[currentHour]).toLocaleString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : `+${currentHour} Hours from Departure`;

  return (
    <div className="card timeline-card">
      <div className="timeline-header">
        <div className="timeline-title-row">
          <div className="timeline-time-badge">
            <span className="hour-pill">T + {currentHour}h</span>
            <span className="timestamp-text">{currentTimestampStr}</span>
          </div>

          <div className="metric-toggle-group">
            <span className="metric-label">Heatmap Layer:</span>
            <button
              type="button"
              className={`btn-metric ${activeMetric === "risk" ? "active" : ""}`}
              onClick={() => onChangeMetric("risk")}
            >
              <AlertCircle size={13} className="mr-1" />
              Composite Hazard
            </button>
            <button
              type="button"
              className={`btn-metric ${activeMetric === "wind" ? "active" : ""}`}
              onClick={() => onChangeMetric("wind")}
            >
              <Wind size={13} className="mr-1" />
              Wind
            </button>
            <button
              type="button"
              className={`btn-metric ${activeMetric === "rain" ? "active" : ""}`}
              onClick={() => onChangeMetric("rain")}
            >
              <CloudRain size={13} className="mr-1" />
              Rain
            </button>
            <button
              type="button"
              className={`btn-metric ${activeMetric === "snow" ? "active" : ""}`}
              onClick={() => onChangeMetric("snow")}
            >
              <Snowflake size={13} className="mr-1" />
              Snow
            </button>
          </div>
        </div>

        <div className="timeline-controls-row">
          <button
            type="button"
            className="btn-control"
            onClick={togglePlay}
            title={isPlaying ? "Pause Forecast" : "Play Forecast Animation"}
          >
            {isPlaying ? <Pause size={16} /> : <Play size={16} />}
            <span>{isPlaying ? "Pause" : "Animate"}</span>
          </button>

          <button
            type="button"
            className="btn-control btn-control-subtle"
            onClick={resetTimeline}
            title="Reset to Departure Hour (0h)"
          >
            <RotateCcw size={15} />
          </button>

          <div className="slider-wrapper">
            <input
              type="range"
              min={0}
              max={maxHours}
              value={currentHour}
              onChange={(e) => {
                setIsPlaying(false);
                onChangeHour(Number(e.target.value));
              }}
              className="timeline-slider"
            />
            <div className="slider-ticks">
              <span>0h (Departure)</span>
              <span>12h</span>
              <span>24h</span>
              <span>36h</span>
              <span>48h Forecast</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

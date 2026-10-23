export const RISK_COLORS = {
  LOW: "#10b981",
  MODERATE: "#f59e0b",
  HIGH: "#f97316",
  SEVERE: "#ef4444",
  NO_TRAVEL: "#7f1d1d",
};

export const RISK_BG_LIGHT = {
  LOW: "#ecfdf5",
  MODERATE: "#fffbeb",
  HIGH: "#fff7ed",
  SEVERE: "#fef2f2",
  NO_TRAVEL: "#450a0a",
};

export const RISK_LABELS = {
  LOW: "Low Risk",
  MODERATE: "Moderate Risk",
  HIGH: "High Risk",
  SEVERE: "Severe Hazard",
  NO_TRAVEL: "No Travel Advised",
};

export function formatWeight(lbs) {
  if (!lbs && lbs !== 0) return "0 lb";
  return `${Number(lbs).toLocaleString()} lb`;
}

export function formatMiles(miles) {
  if (!miles && miles !== 0) return "0 mi";
  return `${Number(miles).toFixed(1)} mi`;
}

export function formatDateTime(isoString) {
  if (!isoString) return "";
  try {
    const d = new Date(isoString);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
}

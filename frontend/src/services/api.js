const API_BASE = "/api";

export async function searchGeocode(query) {
  if (!query || query.trim().length < 2) return [];
  try {
    const res = await fetch(`${API_BASE}/geocode/?q=${encodeURIComponent(query.trim())}`);
    if (!res.ok) throw new Error(`Geocoding HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("Geocoding lookup error:", err);
    return [];
  }
}

export async function analyzeRoutes(payload) {
  const res = await fetch(`${API_BASE}/routes/analyze/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.error || `Analysis failed with status ${res.status}`);
  }

  return await res.json();
}

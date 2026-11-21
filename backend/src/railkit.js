const RAILKIT_BASE = "https://api.railkit.dev/v1";

export async function fetchLiveDelay(trainNumber) {
  const apiKey = process.env.RAILKIT_API_KEY;
  if (!apiKey) {
    return { available: false, message: "RailKit API key not configured" };
  }

  try {
    const res = await fetch(`${RAILKIT_BASE}/trains/${trainNumber}/live`, {
      headers: { Authorization: `Bearer ${apiKey}`, Accept: "application/json" },
    });
    if (!res.ok) {
      return { available: false, message: `RailKit returned ${res.status}` };
    }
    const data = await res.json();
    return {
      available: true,
      live_delay_minutes: data.delay_minutes ?? data.current_delay ?? null,
      status: data.status ?? "unknown",
      last_updated: data.last_updated ?? new Date().toISOString(),
    };
  } catch (err) {
    return { available: false, message: "RailKit API unreachable" };
  }
}

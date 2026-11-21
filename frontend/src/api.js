const API = "/api";

export async function fetchStations() {
  const res = await fetch(`${API}/stations`);
  if (!res.ok) throw new Error("Failed to load stations");
  return res.json();
}

export async function fetchTrains() {
  const res = await fetch(`${API}/trains`);
  if (!res.ok) throw new Error("Failed to load trains");
  return res.json();
}

export async function fetchRouteTrains(source, destination) {
  if (!source || !destination) return [];
  const res = await fetch(`${API}/route-trains?source=${source}&destination=${destination}`);
  if (!res.ok) throw new Error("Failed to load route trains");
  return res.json();
}

export async function checkTrain(body) {
  const res = await fetch(`${API}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

export const DAYS = [
  { value: "Mon", label: "Monday" },
  { value: "Tue", label: "Tuesday" },
  { value: "Wed", label: "Wednesday" },
  { value: "Thu", label: "Thursday" },
  { value: "Fri", label: "Friday" },
  { value: "Sat", label: "Saturday" },
  { value: "Sun", label: "Sunday" },
];

export function dayFromDate(dateStr) {
  if (!dateStr) return "Mon";
  const d = new Date(dateStr + "T12:00:00");
  return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][d.getDay()];
}

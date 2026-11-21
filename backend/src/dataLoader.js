import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = path.join(__dirname, "..", "..", "data", "railsense.db");

let dbInstance = null;

export function getDb() {
  if (!dbInstance) {
    dbInstance = new Database(DB_PATH);
    dbInstance.pragma("foreign_keys = ON");
    dbInstance.pragma("journal_mode = WAL");
  }
  return dbInstance;
}

let cache = null;

export function loadData() {
  if (cache) return cache;
  const db = getDb();

  const stationsRaw = db.prepare("SELECT * FROM stations").all();
  const stations = stationsRaw.map((s) => ({
    ...s,
    is_junction: Boolean(s.is_junction),
  }));

  const trains = db.prepare("SELECT * FROM trains").all();
  const segments = db.prepare("SELECT * FROM segments ORDER BY train_number, stop_sequence").all();
  const delayProfile = db.prepare("SELECT * FROM delay_profile").all();
  const seatAvailability = db.prepare("SELECT * FROM seat_availability").all();
  const busRoutes = db.prepare("SELECT * FROM bus_routes").all();

  const stationMap = Object.fromEntries(stations.map((s) => [s.station_code, s]));
  const trainMap = Object.fromEntries(trains.map((t) => [t.train_number, t]));

  const segmentsByTrain = {};
  for (const seg of segments) {
    if (!segmentsByTrain[seg.train_number]) segmentsByTrain[seg.train_number] = [];
    segmentsByTrain[seg.train_number].push(seg);
  }

  const delayByTrainDay = {};
  for (const d of delayProfile) {
    delayByTrainDay[`${d.train_number}:${d.day_of_week}`] = Number(d.avg_delay_minutes);
  }

  const seatsByTrainDayClass = {};
  for (const s of seatAvailability) {
    seatsByTrainDayClass[`${s.train_number}:${s.day_of_week}:${s.class}`] = Number(s.available_seats);
  }

  cache = {
    stations,
    trains,
    segments,
    delayProfile,
    seatAvailability,
    busRoutes,
    stationMap,
    trainMap,
    segmentsByTrain,
    delayByTrainDay,
    seatsByTrainDayClass,
  };
  return cache;
}

const stmtDelay = () => getDb().prepare("SELECT avg_delay_minutes FROM delay_profile WHERE train_number = ? AND day_of_week = ?");
const stmtSeats = () => getDb().prepare("SELECT available_seats FROM seat_availability WHERE train_number = ? AND day_of_week = ? AND class = ?");

export function getPredictedDelay(trainNumber, day) {
  const row = stmtDelay().get(String(trainNumber), String(day));
  if (!row) return null;
  return Number(row.avg_delay_minutes);
}

export function getAvailableSeats(trainNumber, day, travelClass) {
  const row = stmtSeats().get(String(trainNumber), String(day), String(travelClass));
  if (!row) return null;
  return Number(row.available_seats);
}

export function parseTimeToMinutes(t) {
  if (!t || !t.trim()) return null;
  const [h, m] = t.split(":").map(Number);
  return h * 60 + m;
}

export function minutesToTime(mins) {
  mins = ((mins % (24 * 60)) + 24 * 60) % (24 * 60);
  const h = Math.floor(mins / 60);
  const m = Math.round(mins % 60);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

export function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.asin(Math.sqrt(a));
}


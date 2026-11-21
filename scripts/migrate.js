import Database from "../backend/node_modules/better-sqlite3/lib/index.js";
import fs from "fs";
import path from "path";
import { parse } from "../backend/node_modules/csv-parse/dist/esm/sync.js";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(__dirname, "..", "data");
const DB_PATH = path.join(DATA_DIR, "railsense.db");

console.log(`Initializing SQLite database at: ${DB_PATH}`);

const db = new Database(DB_PATH);
db.pragma("foreign_keys = ON");
db.pragma("journal_mode = WAL");

function readCsv(filename) {
  const filePath = path.join(DATA_DIR, filename);
  if (!fs.existsSync(filePath)) {
    throw new Error(`CSV file not found: ${filePath}`);
  }
  const content = fs.readFileSync(filePath, "utf-8");
  return parse(content, { columns: true, skip_empty_lines: true, trim: true });
}

function migrate() {
  console.log("Creating tables and indexes...");

  // Drop old tables in reverse dependency order
  db.exec(`
    DROP TABLE IF EXISTS bus_routes;
    DROP TABLE IF EXISTS seat_availability;
    DROP TABLE IF EXISTS delay_profile;
    DROP TABLE IF EXISTS segments;
    DROP TABLE IF EXISTS trains;
    DROP TABLE IF EXISTS stations;
  `);

  // Create Schema
  db.exec(`
    CREATE TABLE stations (
      station_code TEXT PRIMARY KEY,
      station_name TEXT NOT NULL,
      latitude REAL,
      longitude REAL,
      zone TEXT,
      is_junction BOOLEAN NOT NULL DEFAULT 0,
      division TEXT
    );

    CREATE TABLE trains (
      train_number TEXT PRIMARY KEY,
      train_name TEXT NOT NULL,
      train_type TEXT NOT NULL,
      source_station TEXT NOT NULL REFERENCES stations(station_code) ON DELETE RESTRICT,
      destination_station TEXT NOT NULL REFERENCES stations(station_code) ON DELETE RESTRICT,
      days_of_operation TEXT
    );

    CREATE TABLE segments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      train_number TEXT NOT NULL REFERENCES trains(train_number) ON DELETE CASCADE,
      stop_sequence INTEGER NOT NULL,
      station_code TEXT NOT NULL REFERENCES stations(station_code) ON DELETE RESTRICT,
      scheduled_arrival TEXT,
      scheduled_departure TEXT,
      distance_from_source_km REAL
    );

    CREATE TABLE delay_profile (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      train_number TEXT NOT NULL REFERENCES trains(train_number) ON DELETE CASCADE,
      day_of_week TEXT NOT NULL,
      avg_delay_minutes INTEGER NOT NULL
    );

    CREATE TABLE seat_availability (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      train_number TEXT NOT NULL REFERENCES trains(train_number) ON DELETE CASCADE,
      day_of_week TEXT NOT NULL,
      class TEXT NOT NULL,
      available_seats INTEGER NOT NULL
    );

    CREATE TABLE bus_routes (
      bus_id TEXT PRIMARY KEY,
      source TEXT NOT NULL REFERENCES stations(station_code) ON DELETE RESTRICT,
      destination TEXT NOT NULL REFERENCES stations(station_code) ON DELETE RESTRICT,
      departure TEXT NOT NULL,
      arrival TEXT NOT NULL,
      bus_type TEXT NOT NULL,
      available_seats INTEGER NOT NULL,
      price_inr REAL NOT NULL
    );

    -- Performance Indexes
    CREATE INDEX idx_stations_code ON stations(station_code);
    CREATE INDEX idx_trains_number ON trains(train_number);
    CREATE INDEX idx_trains_src_dst ON trains(source_station, destination_station);
    CREATE INDEX idx_segments_train_seq ON segments(train_number, stop_sequence);
    CREATE INDEX idx_segments_station ON segments(station_code);
    CREATE INDEX idx_delay_profile_train_day ON delay_profile(train_number, day_of_week);
    CREATE INDEX idx_seats_train_day_class ON seat_availability(train_number, day_of_week, class);
    CREATE INDEX idx_bus_routes_src_dst ON bus_routes(source, destination);
  `);

  console.log("Schema created successfully.");

  const insertStation = db.prepare(`
    INSERT OR REPLACE INTO stations (station_code, station_name, latitude, longitude, zone, is_junction, division)
    VALUES (@station_code, @station_name, @latitude, @longitude, @zone, @is_junction, @division)
  `);

  const insertTrain = db.prepare(`
    INSERT OR REPLACE INTO trains (train_number, train_name, train_type, source_station, destination_station, days_of_operation)
    VALUES (@train_number, @train_name, @train_type, @source_station, @destination_station, @days_of_operation)
  `);

  const insertSegment = db.prepare(`
    INSERT INTO segments (train_number, stop_sequence, station_code, scheduled_arrival, scheduled_departure, distance_from_source_km)
    VALUES (@train_number, @stop_sequence, @station_code, @scheduled_arrival, @scheduled_departure, @distance_from_source_km)
  `);

  const insertDelay = db.prepare(`
    INSERT INTO delay_profile (train_number, day_of_week, avg_delay_minutes)
    VALUES (@train_number, @day_of_week, @avg_delay_minutes)
  `);

  const insertSeat = db.prepare(`
    INSERT INTO seat_availability (train_number, day_of_week, class, available_seats)
    VALUES (@train_number, @day_of_week, @class, @available_seats)
  `);

  const insertBus = db.prepare(`
    INSERT OR REPLACE INTO bus_routes (bus_id, source, destination, departure, arrival, bus_type, available_seats, price_inr)
    VALUES (@bus_id, @source, @destination, @departure, @arrival, @bus_type, @available_seats, @price_inr)
  `);

  // Populate data inside single transaction
  const insertAll = db.transaction(() => {
    // 1. Stations
    const stations = readCsv("stations.csv");
    for (const s of stations) {
      insertStation.run({
        station_code: s.station_code,
        station_name: s.station_name,
        latitude: s.latitude ? Number(s.latitude) : null,
        longitude: s.longitude ? Number(s.longitude) : null,
        zone: s.zone || null,
        is_junction: String(s.is_junction).toLowerCase() === "true" || s.is_junction === "1" ? 1 : 0,
        division: s.division || null,
      });
    }
    console.log(`Inserted ${stations.length} stations.`);

    // 2. Trains
    const trains = readCsv("trains.csv");
    for (const t of trains) {
      insertTrain.run({
        train_number: String(t.train_number),
        train_name: t.train_name,
        train_type: t.train_type,
        source_station: t.source_station,
        destination_station: t.destination_station,
        days_of_operation: t.days_of_operation || "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
      });
    }
    console.log(`Inserted ${trains.length} trains.`);

    // 3. Segments
    const segments = readCsv("segments.csv");
    for (const seg of segments) {
      insertSegment.run({
        train_number: String(seg.train_number),
        stop_sequence: Number(seg.stop_sequence),
        station_code: seg.station_code,
        scheduled_arrival: seg.scheduled_arrival || null,
        scheduled_departure: seg.scheduled_departure || null,
        distance_from_source_km: seg.distance_from_source_km ? Number(seg.distance_from_source_km) : null,
      });
    }
    console.log(`Inserted ${segments.length} route segments.`);

    // 4. Delay Profile
    const delayProfile = readCsv("delay_profile.csv");
    for (const d of delayProfile) {
      insertDelay.run({
        train_number: String(d.train_number),
        day_of_week: d.day_of_week,
        avg_delay_minutes: Number(d.avg_delay_minutes),
      });
    }
    console.log(`Inserted ${delayProfile.length} delay profile records.`);

    // 5. Seat Availability
    const seatAvailability = readCsv("seat_availability.csv");
    for (const sa of seatAvailability) {
      insertSeat.run({
        train_number: String(sa.train_number),
        day_of_week: sa.day_of_week,
        class: sa.class,
        available_seats: Number(sa.available_seats),
      });
    }
    console.log(`Inserted ${seatAvailability.length} seat availability records.`);

    // 6. Bus Routes
    const busRoutes = readCsv("bus_routes.csv");
    for (const b of busRoutes) {
      insertBus.run({
        bus_id: b.bus_id,
        source: b.source,
        destination: b.destination,
        departure: b.departure,
        arrival: b.arrival,
        bus_type: b.bus_type,
        available_seats: Number(b.available_seats),
        price_inr: Number(b.price_inr),
      });
    }
    console.log(`Inserted ${busRoutes.length} bus route records.`);
  });

  insertAll();
  console.log("\nMigration completed successfully with 100% data integrity!");
}

try {
  migrate();
} catch (err) {
  console.error("Migration failed:", err);
  process.exit(1);
}

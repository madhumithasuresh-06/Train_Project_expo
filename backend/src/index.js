import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(__dirname, "..", "..", ".env") });
dotenv.config({ path: path.join(__dirname, "..", ".env") });
import express from "express";
import cors from "cors";
import { loadData } from "./dataLoader.js";
import { buildGraph } from "./graph.js";
import { getPredictedDelay, recommend } from "./recommendation.js";
import { fetchLiveDelay } from "./railkit.js";

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

loadData();
const graph = buildGraph();
console.log(`Graph loaded: ${graph.edgeCount} edges across ${graph.stationCount} stations`);

const VALID_DAYS = new Set(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]);

app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", graph_edges: graph.edgeCount });
});

app.get("/api/stations", (_req, res) => {
  const { stations } = loadData();
  res.json(stations);
});

app.get("/api/trains", (_req, res) => {
  const { trains } = loadData();
  res.json(trains);
});

app.get("/api/route-trains", (req, res) => {
  const { source, destination } = req.query;
  if (!source || !destination) return res.json([]);
  
  const { segmentsByTrain, trains } = loadData();
  const validTrainNumbers = new Set();
  
  for (const [trainNumber, stops] of Object.entries(segmentsByTrain)) {
    const srcIdx = stops.findIndex(s => s.station_code === source);
    const dstIdx = stops.findIndex(s => s.station_code === destination);
    if (srcIdx !== -1 && dstIdx !== -1 && srcIdx < dstIdx) {
      validTrainNumbers.add(Number(trainNumber));
    }
  }
  
  const validTrains = trains.filter(t => validTrainNumbers.has(Number(t.train_number)));
  res.json(validTrains);
});

app.get("/api/predict-delay", async (req, res) => {
  const { train_number, day } = req.query;
  if (!train_number || !day) {
    return res.status(400).json({ error: "train_number and day are required" });
  }
  if (!VALID_DAYS.has(day)) {
    return res.status(400).json({ error: `Invalid day. Use one of: ${[...VALID_DAYS].join(", ")}` });
  }
  const { delay, explanations } = await getPredictedDelay(train_number, day);
  if (delay === null) {
    return res.status(404).json({ error: `No delay profile for train ${train_number} on ${day}` });
  }
  res.json({ train_number, day, predicted_delay_minutes: delay, explanations });
});

app.post("/api/recommend", async (req, res) => {
  const { source_station, destination_station, train_number, day, threshold_minutes, travel_class, manual_delay_minutes } = req.body;

  if (!source_station || !destination_station || !train_number || !day || !travel_class) {
    return res.status(400).json({ error: "source_station, destination_station, train_number, day, and travel_class are required" });
  }
  if (!VALID_DAYS.has(day)) {
    return res.status(400).json({ error: `Invalid day. Use one of: ${[...VALID_DAYS].join(", ")}` });
  }
  const threshold = threshold_minutes ?? 15;

  const result = await recommend({
    sourceStation: source_station,
    destinationStation: destination_station,
    trainNumber: String(train_number),
    day,
    thresholdMinutes: Number(threshold),
    travelClass: travel_class,
    manualDelayMinutes: manual_delay_minutes !== undefined ? Number(manual_delay_minutes) : undefined,
  });

  if (result.error) {
    return res.status(result.status || 400).json({ error: result.error });
  }

  const liveCheck = await fetchLiveDelay(String(train_number));
  res.json({ ...result, live_check: liveCheck });
});

app.get("/api/live-delay", async (req, res) => {
  const { train_number } = req.query;
  if (!train_number) {
    return res.status(400).json({ error: "train_number is required" });
  }
  const predicted = req.query.day ? await getPredictedDelay(String(train_number), req.query.day) : null;
  const live = await fetchLiveDelay(String(train_number));
  res.json({ train_number, predicted_delay_minutes: predicted?.delay, live_check: live });
});

app.listen(PORT, () => {
  console.log(`RailSense API running on http://localhost:${PORT}`);
});

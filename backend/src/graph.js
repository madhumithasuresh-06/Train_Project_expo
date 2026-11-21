import { loadData } from "./dataLoader.js";

export function buildGraph() {
  const { segmentsByTrain, trainMap } = loadData();
  const edges = [];

  for (const [trainNumber, stops] of Object.entries(segmentsByTrain)) {
    const train = trainMap[trainNumber];
    if (!train) continue;
    for (let i = 0; i < stops.length - 1; i++) {
      edges.push({
        train_number: trainNumber,
        train_name: train.train_name,
        train_type: train.train_type,
        from: stops[i].station_code,
        to: stops[i + 1].station_code,
        departure: stops[i].scheduled_departure,
        arrival: stops[i + 1].scheduled_arrival,
      });
    }
  }

  const adjacency = {};
  for (const e of edges) {
    if (!adjacency[e.from]) adjacency[e.from] = [];
    adjacency[e.from].push(e);
  }

  return { edges, adjacency, edgeCount: edges.length, stationCount: Object.keys(adjacency).length };
}

import { loadData, parseTimeToMinutes, minutesToTime, haversineKm, getAvailableSeats } from "./dataLoader.js";

const EXPRESS_TYPES = new Set(["express", "superfast"]);
const LOCAL_TYPES = new Set(["local", "suburban", "passenger"]);
const TRANSFER_BUFFER = 15;
const NEARBY_RADIUS_KM = 20;

function getTrainStops(trainNumber) {
  const { segmentsByTrain } = loadData();
  return segmentsByTrain[trainNumber] || [];
}

function getStopIndex(stops, stationCode) {
  return stops.findIndex((s) => s.station_code === stationCode);
}

function getScheduledArrivalAt(stops, stationCode) {
  const stop = stops.find((s) => s.station_code === stationCode);
  if (!stop) return null;
  return parseTimeToMinutes(stop.scheduled_arrival || stop.scheduled_departure);
}

function getScheduledDepartureAt(stops, stationCode) {
  const stop = stops.find((s) => s.station_code === stationCode);
  if (!stop) return null;
  return parseTimeToMinutes(stop.scheduled_departure || stop.scheduled_arrival);
}

function buildItinerary(legs) {
  const stops = [];
  for (const leg of legs) {
    const legStops = getTrainStops(leg.trainNumber);
    const fromIdx = getStopIndex(legStops, leg.from);
    const toIdx = getStopIndex(legStops, leg.to);
    if (fromIdx === -1 || toIdx === -1) continue;
    const slice = legStops.slice(fromIdx, toIdx + 1);
    for (const s of slice) {
      stops.push({
        station_code: s.station_code,
        scheduled_arrival: s.scheduled_arrival,
        scheduled_departure: s.scheduled_departure,
        train_number: leg.trainNumber,
        train_name: leg.trainName,
        train_type: leg.trainType,
      });
    }
  }
  return stops;
}

function journeyDuration(fromMin, toMin) {
  if (fromMin === null || toMin === null) return Infinity;
  let dur = toMin - fromMin;
  if (dur < 0) dur += 24 * 60;
  return dur;
}

function normalizeComparison(value, reference) {
  let adj = value;
  if (adj < reference) adj += 24 * 60;
  return adj;
}

function findDirectTrains(source, destination, allowedTypes, deadlineMinutes, day, travelClass) {
  const { trains } = loadData();
  const results = [];

  for (const train of trains) {
    if (!allowedTypes.has(train.train_type)) continue;
    const stops = getTrainStops(train.train_number);
    const srcIdx = getStopIndex(stops, source);
    const dstIdx = getStopIndex(stops, destination);
    if (srcIdx === -1 || dstIdx === -1 || srcIdx >= dstIdx) continue;

    const depMin = getScheduledDepartureAt(stops, source);
    const arrMin = getScheduledArrivalAt(stops, destination);
    if (depMin === null || arrMin === null) continue;

    const arrAdj = normalizeComparison(arrMin, depMin);
    const deadlineAdj = deadlineMinutes !== null ? normalizeComparison(deadlineMinutes, depMin) : null;
    if (deadlineAdj !== null && arrAdj > deadlineAdj) continue;
    
    const seats = getAvailableSeats(train.train_number, day, travelClass);
    if (seats === null || seats <= 0) continue;
    
    if (String(train.train_number) === String(globalThis._bookedTrainNumber || "")) continue;

    const duration = journeyDuration(depMin, arrMin);
    results.push({
      level: allowedTypes === EXPRESS_TYPES ? 1 : 2,
      trains: [{
        trainNumber: train.train_number,
        trainName: train.train_name,
        trainType: train.train_type,
        from: source,
        to: destination,
      }],
      departure: minutesToTime(depMin),
      arrival: minutesToTime(arrMin),
      totalDurationMinutes: duration,
      availableSeats: seats,
      transfers: 0,
      reason: allowedTypes === EXPRESS_TYPES
        ? "Level 1 — direct express/superfast train"
        : "Level 2 — local/suburban train, no direct express available",
      itinerary: buildItinerary([{
        trainNumber: train.train_number,
        trainName: train.train_name,
        trainType: train.train_type,
        from: source,
        to: destination,
      }]),
    });
  }

  results.sort((a, b) => a.totalDurationMinutes - b.totalDurationMinutes);
  return results;
}

function findNearbyStations(stationCode, radiusKm) {
  const { stations, stationMap } = loadData();
  const origin = stationMap[stationCode];
  if (!origin) return [];
  return stations
    .filter((s) => s.station_code !== stationCode)
    .map((s) => ({
      ...s,
      distance_km: haversineKm(Number(origin.latitude), Number(origin.longitude), Number(s.latitude), Number(s.longitude)),
    }))
    .filter((s) => s.distance_km <= radiusKm && s.distance_km > 0.5)
    .sort((a, b) => a.distance_km - b.distance_km)
    .slice(0, 5);
}

function findConnectingTrains(from, to, deadlineMinutes, day, travelClass) {
  let results = findDirectTrains(from, to, EXPRESS_TYPES, deadlineMinutes, day, travelClass);
  if (results.length === 0) {
    results = findDirectTrains(from, to, LOCAL_TYPES, deadlineMinutes, day, travelClass);
  }
  return results;
}

function findCombinedJourneys(source, destination, deadlineMinutes, day, travelClass) {
  const results = [];
  const nearbySource = findNearbyStations(source, NEARBY_RADIUS_KM);
  const { stations } = loadData();
  const junctionHubs = stations
    .filter((s) => s.is_junction === true || String(s.is_junction).toLowerCase() === "true")
    .map((s) => s.station_code);
  const hubStations = [...new Set([
    ...nearbySource.map((s) => s.station_code),
    ...junctionHubs,
  ])];

  for (const hub of hubStations) {
    if (hub === source || hub === destination) continue;
    const localLegs = findDirectTrains(source, hub, LOCAL_TYPES, null, day, travelClass);
    const connectLegs = findConnectingTrains(hub, destination, null, day, travelClass);

    for (const local of localLegs.slice(0, 3)) {
      for (const connect of connectLegs.slice(0, 3)) {
        const localDep = parseTimeToMinutes(local.departure);
        const localArr = parseTimeToMinutes(local.arrival);
        const connectDep = parseTimeToMinutes(connect.departure);
        const connectArr = parseTimeToMinutes(connect.arrival);

        const t1End = normalizeComparison(localArr, localDep);
        let t2Start = normalizeComparison(connectDep, localDep);
        if (t2Start - t1End < TRANSFER_BUFFER) continue;

        const connectArrAdj = normalizeComparison(connectArr, localDep);
        if (deadlineMinutes !== null) {
          const deadlineAdj = normalizeComparison(deadlineMinutes, localDep);
          if (connectArrAdj > deadlineAdj) continue;
        }

        const isExpressConnect = EXPRESS_TYPES.has(connect.trains[0].trainType);
        const waitTimeMinutes = t2Start - t1End;
        results.push({
          level: 3,
          trains: [...local.trains, ...connect.trains],
          departure: local.departure,
          arrival: connect.arrival,
          totalDurationMinutes: connectArrAdj - localDep + TRANSFER_BUFFER,
          availableSeats: Math.min(local.availableSeats, connect.availableSeats),
          transfers: 1,
          hubStation: hub,
          waitTimeMinutes: waitTimeMinutes,
          legs: [
            {
              legIndex: 1,
              train: local.trains[0],
              departure: local.departure,
              arrival: local.arrival,
              from: source,
              to: hub,
              itinerary: buildItinerary([{ ...local.trains[0], from: source, to: hub }])
            },
            {
              legIndex: 2,
              train: connect.trains[0],
              departure: connect.departure,
              arrival: connect.arrival,
              from: hub,
              to: destination,
              itinerary: buildItinerary([{ ...connect.trains[0], from: hub, to: destination }])
            }
          ],
          reason: isExpressConnect
            ? `Level 3 — via hub ${hub} (local + connecting express)`
            : `Level 3 — via hub ${hub} (local + connecting train, no direct express)`,
          itinerary: buildItinerary([
            { ...local.trains[0], from: source, to: hub },
            { ...connect.trains[0], from: hub, to: destination },
          ]),
        });
      }
    }
  }

  const seen = new Set();
  return results
    .filter((r) => {
      const key = r.trains.map((t) => t.trainNumber).join("-");
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .sort((a, b) => a.totalDurationMinutes - b.totalDurationMinutes);
}

export async function getPredictedDelay(trainNumber, day) {
  try {
    const response = await fetch(`http://localhost:8000/predict?train_number=${trainNumber}&day=${day}`);
    if (!response.ok) return { delay: null, explanations: [] };
    const data = await response.json();
    return { delay: data.predicted_delay_minutes, explanations: data.explanations };
  } catch (error) {
    console.error("ML service error:", error);
    // Fallback to static if ML service is down
    const { delayByTrainDay } = loadData();
    const key = `${trainNumber}:${day}`;
    return { delay: delayByTrainDay[key] ?? null, explanations: [] };
  }
}

function findBusAlternatives(source, destination, deadlineMinutes) {
  const { busRoutes } = loadData();
  const results = [];

  for (const bus of busRoutes) {
    if (bus.source !== source || bus.destination !== destination) continue;
    
    const depMin = parseTimeToMinutes(bus.departure);
    const arrMin = parseTimeToMinutes(bus.arrival);
    if (depMin === null || arrMin === null) continue;

    const arrAdj = normalizeComparison(arrMin, depMin);
    const deadlineAdj = deadlineMinutes !== null ? normalizeComparison(deadlineMinutes, depMin) : null;
    if (deadlineAdj !== null && arrAdj > deadlineAdj) continue;
    
    if (Number(bus.available_seats) <= 0) continue;

    const duration = journeyDuration(depMin, arrMin);
    results.push({
      level: 4,
      type: "bus",
      trains: [{ 
        trainNumber: bus.bus_id,
        trainName: bus.bus_type,
        trainType: "bus",
        from: source,
        to: destination,
      }],
      departure: bus.departure,
      arrival: bus.arrival,
      totalDurationMinutes: duration,
      availableSeats: Number(bus.available_seats),
      transfers: 0,
      reason: `Level 4 — Bus alternative (${bus.bus_type})`,
      itinerary: [
        { station_code: source, scheduled_departure: bus.departure, train_number: bus.bus_id, train_name: bus.bus_type, train_type: "bus" },
        { station_code: destination, scheduled_arrival: bus.arrival, train_number: bus.bus_id, train_name: bus.bus_type, train_type: "bus" }
      ],
    });
  }

  results.sort((a, b) => a.totalDurationMinutes - b.totalDurationMinutes);
  return results;
}

export async function recommend({ sourceStation, destinationStation, trainNumber, day, thresholdMinutes, travelClass = "2S", manualDelayMinutes }) {
  const { trainMap, stationMap } = loadData();

  if (!stationMap[sourceStation]) {
    return { error: `Invalid source station: ${sourceStation}`, status: 400 };
  }
  if (!stationMap[destinationStation]) {
    return { error: `Invalid destination station: ${destinationStation}`, status: 400 };
  }
  if (!trainMap[trainNumber]) {
    return { error: `Invalid train number: ${trainNumber}`, status: 400 };
  }

  const { delay: predictedDelay, explanations } = await getPredictedDelay(trainNumber, day);
  if (predictedDelay === null && manualDelayMinutes === undefined) {
    return { error: `No delay profile for train ${trainNumber} on ${day}`, status: 404 };
  }

  const effectiveDelay = manualDelayMinutes !== undefined ? manualDelayMinutes : predictedDelay;

  const bookedTrainData = trainMap[trainNumber];
  const bookedItinerary = buildItinerary([{
    trainNumber: trainNumber,
    trainName: bookedTrainData.train_name,
    trainType: bookedTrainData.train_type,
    from: sourceStation,
    to: destinationStation
  }]);

  if (effectiveDelay <= thresholdMinutes) {
    return {
      status: "on_time",
      message: manualDelayMinutes !== undefined ? `Manual override: Proceed with booked train` : "Proceed with booked train",
      predicted_delay_minutes: effectiveDelay,
      explanations,
      threshold_minutes: thresholdMinutes,
      booked_train: bookedTrainData,
      booked_itinerary: bookedItinerary,
    };
  }

  const bookedStops = getTrainStops(trainNumber);
  globalThis._bookedTrainNumber = trainNumber;
  const srcIdx = getStopIndex(bookedStops, sourceStation);
  const dstIdx = getStopIndex(bookedStops, destinationStation);
  if (srcIdx === -1 || dstIdx === -1) {
    return { error: "Booked train does not serve the requested route", status: 400 };
  }

  const scheduledArr = getScheduledArrivalAt(bookedStops, destinationStation);
  const delayedEta = scheduledArr + effectiveDelay;

  let alternatives = findDirectTrains(sourceStation, destinationStation, EXPRESS_TYPES, delayedEta, day, travelClass);
  if (alternatives.length === 0) {
    alternatives = findDirectTrains(sourceStation, destinationStation, LOCAL_TYPES, delayedEta, day, travelClass);
  }
  if (alternatives.length === 0) {
    alternatives = findCombinedJourneys(sourceStation, destinationStation, delayedEta, day, travelClass);
  }
  if (alternatives.length === 0) {
    alternatives = findBusAlternatives(sourceStation, destinationStation, delayedEta);
  }

  return {
    status: "delayed",
    message: manualDelayMinutes !== undefined 
      ? `Manual delay of ${effectiveDelay} min exceeds threshold of ${thresholdMinutes} min` 
      : `Predicted delay of ${effectiveDelay} min exceeds threshold of ${thresholdMinutes} min`,
    predicted_delay_minutes: effectiveDelay,
    explanations,
    threshold_minutes: thresholdMinutes,
    delayed_eta: minutesToTime(delayedEta),
    booked_train: bookedTrainData,
    booked_itinerary: bookedItinerary,
    alternatives: alternatives.slice(0, 3),
  };
}

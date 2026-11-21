import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { fetchStations, fetchTrains, fetchRouteTrains, checkTrain, dayFromDate } from "./api";
import Autocomplete from "./components/Autocomplete";
import RouteTimeline, { OnTimeCard, LiveDelayChip } from "./components/Results";
import RouteMap from "./components/RouteMap";

export default function App() {
  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [train, setTrain] = useState("");
  const [travelDate, setTravelDate] = useState(new Date().toISOString().slice(0, 10));
  const [threshold, setThreshold] = useState(15);
  const [travelClass, setTravelClass] = useState("SL");
  const [manualDelay, setManualDelay] = useState("");
  const [selectedAltIndex, setSelectedAltIndex] = useState(0);

  const { data: stations = [] } = useQuery({ queryKey: ["stations"], queryFn: fetchStations });
  const { data: allTrains = [] } = useQuery({ queryKey: ["trains"], queryFn: fetchTrains });

  const { data: routeTrains = [] } = useQuery({ 
    queryKey: ["routeTrains", source, destination], 
    queryFn: () => fetchRouteTrains(source, destination),
    enabled: !!source && !!destination
  });

  const sortedStations = [...stations].sort((a, b) => a.station_name.localeCompare(b.station_name));
  const displayTrains = (source && destination) ? routeTrains : allTrains;
  const sortedTrains = [...displayTrains].sort((a, b) => a.train_name.localeCompare(b.train_name));

  const stationMap = Object.fromEntries(stations.map((s) => [s.station_code, s]));

  const mutation = useMutation({
    mutationFn: checkTrain,
    onSuccess: () => setSelectedAltIndex(0),
  });

  function handleSubmit(e) {
    e.preventDefault();
    if (!source || !destination || !train) return;
    mutation.mutate({
      source_station: source,
      destination_station: destination,
      train_number: train,
      day: dayFromDate(travelDate),
      threshold_minutes: Number(threshold),
      travel_class: travelClass,
      manual_delay_minutes: manualDelay ? Number(manualDelay) : undefined,
    });
  }

  const result = mutation.data;

  return (
    <div className="min-h-screen">
      <header className="border-b border-rail-800/30 bg-navy-950/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
          <motion.div 
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-10 h-10 rounded-xl bg-gradient-to-br from-rail-400 to-rail-600 flex items-center justify-center shadow-lg shadow-rail-500/50"
          >
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </motion.div>
          <div>
            <h1 className="font-display text-xl font-bold tracking-tight">RailSense</h1>
            <p className="text-xs text-rail-400">Tamil Nadu Railway Assistant</p>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        <section className="rounded-2xl border border-rail-800/30 bg-navy-900/40 p-6 sm:p-8 backdrop-blur">
          <h2 className="font-display text-lg font-semibold text-rail-100 mb-1">Plan your journey</h2>
          <p className="text-sm text-rail-400 mb-6">Check predicted delays and get alternative routes before you travel.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid sm:grid-cols-2 gap-4">
              <Autocomplete
                label="From"
                placeholder="Source station..."
                options={sortedStations}
                value={source}
                onChange={setSource}
                getOptionLabel={(s) => `${s.station_name} (${s.station_code})`}
              />
              <Autocomplete
                label="To"
                placeholder="Destination station..."
                options={sortedStations}
                value={destination}
                onChange={setDestination}
                getOptionLabel={(s) => `${s.station_name} (${s.station_code})`}
              />
            </div>

            <Autocomplete
              label="Your train"
              placeholder="Search by name or number..."
              options={sortedTrains}
              value={train}
              onChange={setTrain}
              renderOption={(t) => `${t.train_name} · #${t.train_number} (${t.train_type})`}
              getOptionLabel={(t) => t.train_number}
            />

            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-medium text-rail-300 mb-1.5 uppercase tracking-wider">Travel date</label>
                <input
                  type="date"
                  value={travelDate}
                  onChange={(e) => setTravelDate(e.target.value)}
                  className="w-full rounded-xl bg-navy-900/80 border border-rail-700/40 px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-rail-500/50 backdrop-blur-md"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-rail-300 mb-1.5 uppercase tracking-wider">Class</label>
                <select
                  value={travelClass}
                  onChange={(e) => setTravelClass(e.target.value)}
                  className="w-full rounded-xl bg-navy-900/80 border border-rail-700/40 px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-rail-500/50 appearance-none backdrop-blur-md"
                >
                  <option value="SL">Sleeper (SL)</option>
                  <option value="3A">3 Tier AC (3A)</option>
                  <option value="2A">2 Tier AC (2A)</option>
                  <option value="1A">First Class (1A)</option>
                  <option value="CC">AC Chair Car (CC)</option>
                  <option value="2S">Second Seating (2S)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-rail-300 mb-1.5 uppercase tracking-wider">Delay threshold (min)</label>
                <input
                  type="number"
                  min={1}
                  max={120}
                  value={threshold}
                  onChange={(e) => setThreshold(e.target.value)}
                  className="w-full rounded-xl bg-navy-900/80 border border-rail-700/40 px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-rail-500/50 backdrop-blur-md"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-rail-300 mb-1.5 uppercase tracking-wider">Manual delay (opt)</label>
                <input
                  type="number"
                  min={0}
                  placeholder="e.g. 20"
                  value={manualDelay}
                  onChange={(e) => setManualDelay(e.target.value)}
                  className="w-full rounded-xl bg-navy-900/80 border border-rail-700/40 px-4 py-3 text-white placeholder:text-rail-600 focus:outline-none focus:ring-2 focus:ring-rail-500/50 backdrop-blur-md"
                />
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={mutation.isPending || !source || !destination || !train}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-rail-500 to-rail-600 hover:from-rail-400 hover:to-rail-500 text-white font-semibold shadow-[0_0_20px_rgba(59,130,246,0.4)] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {mutation.isPending ? "Checking..." : "Check My Train"}
            </motion.button>
          </form>

          {mutation.isError && (
            <div className="mt-4 rounded-xl bg-red-950/40 border border-red-500/30 px-4 py-3 text-sm text-red-300">
              {mutation.error.message}
            </div>
          )}
        </section>

        {result && (
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {result.status === "on_time" ? (
              <div className="space-y-6">
                <OnTimeCard result={result} />
                {result.booked_itinerary && (
                  <div className="space-y-4">
                    <h3 className="font-display text-lg font-semibold text-rail-100">
                      Route map
                    </h3>
                    <RouteMap 
                      stationMap={stationMap} 
                      originalItinerary={result.booked_itinerary} 
                    />
                  </div>
                )}
              </div>
            ) : (
              <>
                <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-950/30 to-navy-950/80 p-6">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Delay anticipated</span>
                      <h2 className="font-display text-2xl font-bold text-amber-200 mt-1">
                        +{result.predicted_delay_minutes} min predicted
                      </h2>
                      {result.explanations && result.explanations.length > 0 && (
                        <div className="mt-3">
                          <details className="group [&_summary::-webkit-details-marker]:hidden">
                            <summary className="flex cursor-pointer items-center gap-1.5 text-sm font-medium text-amber-300 hover:text-amber-200 transition-colors">
                              <span>Why this delay?</span>
                              <svg className="size-4 transition duration-300 group-open:-rotate-180" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                              </svg>
                            </summary>
                            <div className="mt-3 space-y-2 border-l-2 border-amber-500/30 pl-3">
                              {result.explanations.map((exp, i) => (
                                <div key={i} className="flex justify-between items-center text-xs text-amber-100/90 gap-4">
                                  <span>{exp.feature}</span>
                                  <span className="font-mono font-medium text-amber-300">{exp.impact}</span>
                                </div>
                              ))}
                            </div>
                          </details>
                        </div>
                      )}
                      <p className="text-rail-300 mt-3 text-sm">{result.message}</p>
                      <p className="text-sm text-rail-400 mt-1">
                        Revised ETA: <span className="text-white font-medium">{result.delayed_eta}</span>
                      </p>
                    </div>
                    <LiveDelayChip liveCheck={result.live_check} predicted={result.predicted_delay_minutes} />
                  </div>
                </div>

                {result.alternatives?.length > 0 ? (
                  <div className="grid lg:grid-cols-2 gap-6 items-start">
                    <div className="space-y-4">
                      <h3 className="font-display text-lg font-semibold text-rail-100">
                        Recommended alternatives
                      </h3>
                      {result.alternatives.map((alt, i) => (
                        <RouteTimeline 
                          key={i} 
                          alt={alt} 
                          index={i} 
                          stationMap={stationMap} 
                          isSelected={selectedAltIndex === i}
                          onSelect={setSelectedAltIndex}
                        />
                      ))}
                    </div>
                    <div className="space-y-4 lg:sticky lg:top-24">
                      <h3 className="font-display text-lg font-semibold text-rail-100">
                        Route map
                      </h3>
                      <RouteMap 
                        stationMap={stationMap} 
                        originalItinerary={result.booked_itinerary} 
                        alternativeItinerary={result.alternatives[selectedAltIndex]?.itinerary || result.alternatives[0]?.itinerary} 
                      />
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border border-rail-700/30 bg-navy-900/40 p-6 text-center text-rail-400 text-sm">
                    No alternative routes found within the current schedule. Consider adjusting your travel time.
                  </div>
                )}
              </>
            )}

            {result.status === "on_time" && result.live_check && (
              <div className="flex justify-center">
                <LiveDelayChip liveCheck={result.live_check} predicted={result.predicted_delay_minutes} />
              </div>
            )}
          </motion.section>
        )}
      </main>

      <footer className="max-w-4xl mx-auto px-4 py-8 text-center text-xs text-rail-600">
        RailSense · Predictive delay model · Tamil Nadu rail network
      </footer>
    </div>
  );
}

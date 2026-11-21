const TYPE_STYLES = {
  superfast: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  express: "bg-rail-500/20 text-rail-300 border-rail-500/30",
  local: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  suburban: "bg-sky-500/20 text-sky-300 border-sky-500/30",
  passenger: "bg-violet-500/20 text-violet-300 border-violet-500/30",
  bus: "bg-pink-500/20 text-pink-300 border-pink-500/30",
};

function TypeBadge({ type }) {
  const displayType = type || "express";
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-md text-xs font-medium border capitalize ${TYPE_STYLES[displayType] || TYPE_STYLES.express}`}>
      {displayType}
    </span>
  );
}

function formatDuration(mins) {
  if (typeof mins !== "number" || isNaN(mins)) return "—";
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function TimelineStopsList({ itinerary = [], stationMap = {}, isBus = false, accentColor = "text-rail-500" }) {
  return (
    <div className="relative pl-4 border-l-2 border-rail-600/40 space-y-0">
      {itinerary.map((stop, i) => {
        const name = stationMap[stop.station_code]?.station_name || stop.station_code;
        const isLast = i === itinerary.length - 1;
        const trainNumStr = stop.train_number ? `#${stop.train_number}` : "";
        return (
          <div key={i} className="relative pb-4 last:pb-0">
            <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-rail-500 ring-4 ring-navy-900" />
            <div className="flex flex-wrap items-baseline gap-2">
              <span className="font-medium text-white">{name}</span>
              <span className="text-xs text-rail-500 font-mono">{stop.station_code}</span>
            </div>
            <div className="text-xs text-rail-400 mt-0.5 flex gap-3">
              {stop.scheduled_arrival && <span>Arr {stop.scheduled_arrival}</span>}
              {stop.scheduled_departure && <span>Dep {stop.scheduled_departure}</span>}
              {trainNumStr && <span className={isBus ? "text-pink-400" : accentColor}>{trainNumStr}</span>}
            </div>
            {!isLast && i < itinerary.length - 1 && (
              <div className="text-[10px] text-rail-600 mt-1">↓</div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function RouteTimeline({ alt = {}, index = 0, stationMap = {}, isSelected = false, onSelect }) {
  const isBus = alt.type === "bus";
  const isLevel3 = alt.level === 3 || (alt.legs && alt.legs.length > 1);
  
  const cardBg = isBus 
    ? "from-pink-950/40 to-navy-950/90 hover:border-pink-500/40"
    : isLevel3
    ? "from-purple-950/40 via-navy-900/90 to-navy-950/90 hover:border-purple-500/40"
    : "from-navy-900/90 to-navy-950/90 hover:border-rail-500/40";
    
  const trains = alt.trains || [];
  const itinerary = alt.itinerary || [];
  const seats = alt.availableSeats ?? 0;
  const transfers = alt.transfers ?? 0;

  // Level 3 legs data
  const legs = alt.legs || [];
  const hasTwoLegs = isLevel3 && legs.length >= 2;
  const leg1 = hasTwoLegs ? legs[0] : null;
  const leg2 = hasTwoLegs ? legs[1] : null;

  const hubCode = alt.hubStation || leg1?.to || "";
  const hubName = stationMap[hubCode]?.station_name || hubCode || "Hub Station";
  const waitTime = alt.waitTimeMinutes ?? 0;

  return (
    <article
      onClick={() => onSelect && onSelect(index)}
      className={`animate-fade-up rounded-2xl border ${isSelected ? 'ring-2 ring-emerald-500/80 border-emerald-500/80' : 'border-rail-700/30'} bg-gradient-to-br ${cardBg} p-5 shadow-lg shadow-black/20 transition-all duration-300 cursor-pointer`}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <span className={`flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider ${isBus ? 'text-pink-400' : isLevel3 ? 'text-purple-400' : 'text-rail-400'}`}>
            {isBus && (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
              </svg>
            )}
            {isLevel3 && (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            )}
            Option {index + 1} {isBus && " (Bus Fallback)"} {isLevel3 && ` (Hub Connection via ${hubName})`}
          </span>
          <h3 className="font-display text-lg font-semibold text-white mt-0.5">
            {trains.map((t) => t.trainName || t.trainNumber).filter(Boolean).join(" → ") || "Alternative Route"}
          </h3>
          <p className={`text-sm mt-1 ${isBus ? 'text-pink-300' : isLevel3 ? 'text-purple-300' : 'text-rail-400'}`}>{alt.reason}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {trains.map((t, i) => (
            <TypeBadge key={i} type={t.trainType} />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-5 text-sm">
        <div className="rounded-lg bg-navy-950/60 px-3 py-2 shadow-inner shadow-black/20 border border-rail-800/30">
          <div className="text-rail-500 text-xs">Departs</div>
          <div className="font-semibold text-white">{alt.departure || "—"}</div>
        </div>
        <div className="rounded-lg bg-navy-950/60 px-3 py-2 shadow-inner shadow-black/20 border border-rail-800/30">
          <div className="text-rail-500 text-xs">Arrives</div>
          <div className="font-semibold text-white">{alt.arrival || "—"}</div>
        </div>
        <div className="rounded-lg bg-navy-950/60 px-3 py-2 shadow-inner shadow-black/20 border border-rail-800/30">
          <div className="text-rail-500 text-xs">Duration</div>
          <div className="font-semibold text-white">{formatDuration(alt.totalDurationMinutes)}</div>
        </div>
        <div className="rounded-lg bg-navy-950/60 px-3 py-2 shadow-inner shadow-black/20 border border-rail-800/30">
          <div className="text-rail-500 text-xs">Transfers</div>
          <div className="font-semibold text-amber-400">{transfers}</div>
        </div>
        <div className={`rounded-lg px-3 py-2 shadow-inner shadow-black/20 border ${seats > 50 ? 'bg-emerald-950/30 border-emerald-500/20' : (seats > 10 ? 'bg-amber-950/30 border-amber-500/20' : 'bg-red-950/30 border-red-500/20')}`}>
          <div className="text-rail-500 text-xs">Availability</div>
          <div className={`font-semibold ${seats > 50 ? 'text-emerald-400' : (seats > 10 ? 'text-amber-400' : 'text-red-400')}`}>
            {seats > 0 ? `${seats} Seats` : 'Waitlist'}
          </div>
        </div>
      </div>

      {hasTwoLegs ? (
        <div className="space-y-4">
          {/* LEG 1 */}
          <div className="rounded-xl border border-rail-700/30 bg-navy-950/40 p-4">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-rail-800/40">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-rail-500/20 text-rail-300 font-bold text-xs uppercase tracking-wider">Leg 1</span>
                <span className="font-semibold text-white text-sm">{leg1.train?.trainName} (#{leg1.train?.trainNumber})</span>
              </div>
              <TypeBadge type={leg1.train?.trainType} />
            </div>
            <TimelineStopsList itinerary={leg1.itinerary} stationMap={stationMap} accentColor="text-rail-400" />
          </div>

          {/* TRANSFER / LAYOVER BANNER */}
          <div className="rounded-2xl border border-amber-500/40 bg-gradient-to-r from-amber-950/70 via-purple-950/70 to-navy-950/90 p-4 shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-300 font-bold text-lg shadow-inner">
                  🔄
                </div>
                <div>
                  <div className="text-xs font-bold text-amber-400 uppercase tracking-widest flex items-center gap-2">
                    <span>CHANGE TRAINS AT {hubName.toUpperCase()} ({hubCode})</span>
                    <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px]">TRANSFER POINT</span>
                  </div>
                  <div className="text-sm font-semibold text-white mt-1">
                    Get off <span className="text-amber-300">Train #{leg1.train?.trainNumber} ({leg1.train?.trainName})</span>
                    <span className="mx-2 text-rail-400">→</span>
                    Board <span className="text-emerald-300">Train #{leg2.train?.trainNumber} ({leg2.train?.trainName})</span>
                  </div>
                </div>
              </div>
              <div className="rounded-xl bg-navy-950/80 border border-amber-500/30 px-3.5 py-2 text-xs text-amber-200 font-semibold shadow-inner">
                ⏱️ Wait {formatDuration(waitTime)} at {hubName}
              </div>
            </div>
          </div>

          {/* LEG 2 */}
          <div className="rounded-xl border border-rail-700/30 bg-navy-950/40 p-4">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-rail-800/40">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold text-xs uppercase tracking-wider">Leg 2</span>
                <span className="font-semibold text-white text-sm">{leg2.train?.trainName} (#{leg2.train?.trainNumber})</span>
              </div>
              <TypeBadge type={leg2.train?.trainType} />
            </div>
            <TimelineStopsList itinerary={leg2.itinerary} stationMap={stationMap} accentColor="text-emerald-400" />
          </div>
        </div>
      ) : (
        <TimelineStopsList itinerary={itinerary} stationMap={stationMap} isBus={isBus} />
      )}
    </article>
  );
}

export function OnTimeCard({ result = {} }) {
  return (
    <div className="animate-fade-up rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 to-navy-950/80 p-8 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/20 mb-4">
        <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h2 className="font-display text-2xl font-semibold text-emerald-300">You're good to go</h2>
      <p className="text-rail-300 mt-2 max-w-md mx-auto">{result.message}</p>
      <p className="mt-4 text-sm text-rail-400">
        Predicted delay: <span className="text-white font-medium">{result.predicted_delay_minutes ?? 0} min</span>
        {" "}(threshold: {result.threshold_minutes ?? 15} min)
      </p>
      <p className="text-sm text-rail-500 mt-1">
        {result.booked_train?.train_name} · #{result.booked_train?.train_number}
      </p>
    </div>
  );
}

export function LiveDelayChip({ liveCheck, predicted }) {
  if (!liveCheck) return null;
  return (
    <div className="inline-flex items-center gap-2 rounded-full bg-navy-900/80 border border-rail-700/40 px-3 py-1.5 text-xs">
      <span className="text-rail-500">Live vs Predicted</span>
      {liveCheck.available ? (
        <>
          <span className="text-amber-400">{liveCheck.live_delay_minutes ?? "—"} min live</span>
          <span className="text-rail-600">·</span>
          <span className="text-rail-300">{predicted ?? 0} min predicted</span>
        </>
      ) : (
        <span className="text-rail-500 italic">{liveCheck.message}</span>
      )}
    </div>
  );
}

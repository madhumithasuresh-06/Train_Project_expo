import React, { useEffect } from "react";
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Fix Leaflet icon issue in React
import L from "leaflet";
if (typeof window !== "undefined" && L.Icon?.Default?.prototype) {
  delete L.Icon.Default.prototype._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  });
}

function MapBounds({ coords }) {
  const map = useMap();
  useEffect(() => {
    if (coords && coords.length > 0) {
      try {
        const bounds = L.latLngBounds(coords);
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [50, 50] });
        }
      } catch (err) {
        console.warn("Map bounds fit error:", err);
      }
    }
  }, [coords, map]);
  return null;
}

class MapErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.warn("RouteMap render error:", error, errorInfo);
  }
  componentDidUpdate(prevProps) {
    if (this.state.hasError && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ hasError: false, error: null });
    }
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="w-full h-64 rounded-xl border border-rail-700/30 bg-navy-900/40 p-4 flex flex-col items-center justify-center text-rail-400 text-sm gap-2">
          <span>Map view unavailable.</span>
          <span className="text-xs text-rail-600 font-mono">{String(this.state.error?.message || "")}</span>
        </div>
      );
    }
    return this.props.children;
  }
}

function RouteMapContent({ stationMap = {}, originalItinerary = [], alternativeItinerary = [] }) {
  if (!originalItinerary?.length && !alternativeItinerary?.length) return null;

  const originalCoords = (originalItinerary || [])
    .map(stop => stationMap[stop.station_code])
    .filter(s => s && s.latitude != null && s.longitude != null)
    .map(s => [Number(s.latitude), Number(s.longitude)])
    .filter(c => !isNaN(c[0]) && !isNaN(c[1]));

  const alternativeCoords = (alternativeItinerary || [])
    .map(stop => stationMap[stop.station_code])
    .filter(s => s && s.latitude != null && s.longitude != null)
    .map(s => [Number(s.latitude), Number(s.longitude)])
    .filter(c => !isNaN(c[0]) && !isNaN(c[1]));

  const allCoords = [...originalCoords, ...alternativeCoords];
  
  if (allCoords.length === 0) {
    return (
      <div className="w-full h-64 rounded-xl border border-rail-700/30 bg-navy-900/40 flex items-center justify-center text-rail-400 text-sm">
        Map view available for train & bus routes with valid coordinates.
      </div>
    );
  }

  // Generate unique map key based on itinerary station codes
  const mapKey = (originalItinerary || []).map(s => s.station_code).join('-') + '_' + (alternativeItinerary || []).map(s => s.station_code).join('-');

  // Free Esri Dark Gray Basemap (No API key required)
  const tileUrl = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}";
  const attribution = "Tiles © Esri";

  return (
    <div className="w-full h-[400px] rounded-2xl overflow-hidden border border-rail-700/50 shadow-lg shadow-black/40">
      <MapContainer key={mapKey} center={allCoords[0] || [11.1271, 78.6569]} zoom={7} className="w-full h-full" zoomControl={false} style={{ height: "100%", width: "100%", background: "#0f172a" }}>
        <TileLayer
          url={tileUrl}
          attribution={attribution}
        />
        
        {originalCoords.length > 1 && (
          <Polyline positions={originalCoords} pathOptions={{ color: "#ef4444", weight: 3, dashArray: "8, 8" }} />
        )}
        
        {alternativeCoords.length > 1 && (
          <Polyline positions={alternativeCoords} pathOptions={{ color: "#10b981", weight: 4 }} />
        )}

        {/* Plotting original points */}
        {(originalItinerary || []).map((stop, i) => {
          const s = stationMap[stop.station_code];
          if (!s || s.latitude == null || s.longitude == null) return null;
          const lat = Number(s.latitude);
          const lng = Number(s.longitude);
          if (isNaN(lat) || isNaN(lng)) return null;
          const isFirst = i === 0;
          const isLast = i === originalItinerary.length - 1;
          const stationName = s.station_name || stop.station_code;

          return (
            <CircleMarker
              key={`orig-${stop.station_code}-${i}`}
              center={[lat, lng]}
              radius={isFirst || isLast ? 7 : 5}
              pathOptions={{
                color: "#ef4444",
                fillColor: isFirst || isLast ? "#ef4444" : "#0f172a",
                fillOpacity: 1,
                weight: 2,
              }}
            >
              <Popup>
                <div className="p-1 min-w-[150px] font-sans">
                  <div className="font-bold text-sm text-gray-900 leading-snug">
                    {stationName} <span className="text-gray-500 font-mono text-xs">({stop.station_code})</span>
                  </div>
                  <div className="mt-1 inline-block px-1.5 py-0.5 rounded text-[11px] font-semibold bg-red-100 text-red-700">
                    Original Route {isFirst ? " · Origin" : isLast ? " · Destination" : ""}
                  </div>
                  <div className="mt-2 text-xs border-t border-gray-200 pt-1.5 text-gray-700 space-y-0.5">
                    {stop.scheduled_arrival && (
                      <div><span className="font-medium text-gray-500">Arr:</span> {stop.scheduled_arrival}</div>
                    )}
                    {stop.scheduled_departure && (
                      <div><span className="font-medium text-gray-500">Dep:</span> {stop.scheduled_departure}</div>
                    )}
                    {!stop.scheduled_arrival && !stop.scheduled_departure && (
                      <div className="text-gray-400 italic">No schedule time</div>
                    )}
                    {(stop.train_name || stop.train_number) && (
                      <div className="text-[11px] text-gray-500 mt-1 font-mono">
                        {stop.train_name ? `${stop.train_name} ` : ''}{stop.train_number ? `(#${stop.train_number})` : ''}
                      </div>
                    )}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {/* Plotting alternative points */}
        {(alternativeItinerary || []).map((stop, i) => {
          const s = stationMap[stop.station_code];
          if (!s || s.latitude == null || s.longitude == null) return null;
          const lat = Number(s.latitude);
          const lng = Number(s.longitude);
          if (isNaN(lat) || isNaN(lng)) return null;
          const isFirst = i === 0;
          const isLast = i === alternativeItinerary.length - 1;
          const stationName = s.station_name || stop.station_code;

          return (
            <CircleMarker
              key={`alt-${stop.station_code}-${i}`}
              center={[lat, lng]}
              radius={isFirst || isLast ? 8 : 6}
              pathOptions={{
                color: "#10b981",
                fillColor: "#10b981",
                fillOpacity: 0.9,
                weight: 2,
              }}
            >
              <Popup>
                <div className="p-1 min-w-[150px] font-sans">
                  <div className="font-bold text-sm text-gray-900 leading-snug">
                    {stationName} <span className="text-gray-500 font-mono text-xs">({stop.station_code})</span>
                  </div>
                  <div className="mt-1 inline-block px-1.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                    Alternative Route {isFirst ? " · Origin" : isLast ? " · Destination" : ""}
                  </div>
                  <div className="mt-2 text-xs border-t border-gray-200 pt-1.5 text-gray-700 space-y-0.5">
                    {stop.scheduled_arrival && (
                      <div><span className="font-medium text-gray-500">Arr:</span> {stop.scheduled_arrival}</div>
                    )}
                    {stop.scheduled_departure && (
                      <div><span className="font-medium text-gray-500">Dep:</span> {stop.scheduled_departure}</div>
                    )}
                    {!stop.scheduled_arrival && !stop.scheduled_departure && (
                      <div className="text-gray-400 italic">No schedule time</div>
                    )}
                    {(stop.train_name || stop.train_number) && (
                      <div className="text-[11px] text-gray-500 mt-1 font-mono">
                        {stop.train_name ? `${stop.train_name} ` : ''}{stop.train_number ? `(#${stop.train_number})` : ''}
                      </div>
                    )}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        <MapBounds coords={allCoords} />
      </MapContainer>
    </div>
  );
}

export default function RouteMap(props) {
  const resetKey = (props.originalItinerary || []).map(s => s.station_code).join('-') + '_' + (props.alternativeItinerary || []).map(s => s.station_code).join('-');
  return (
    <MapErrorBoundary resetKey={resetKey}>
      <RouteMapContent {...props} />
    </MapErrorBoundary>
  );
}

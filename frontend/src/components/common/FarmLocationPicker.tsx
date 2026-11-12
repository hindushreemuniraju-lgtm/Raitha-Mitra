import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  AlertCircle,
  CheckCircle2,
  LocateFixed,
  MapPin,
  Navigation,
  RefreshCw,
  Square,
} from "lucide-react";
import { useLiveGps } from "@/hooks/useLiveGps";

export interface FarmLocationValue {
  state: string;
  district: string;
  taluk: string;
  village: string;
  location_address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  gps_consent: boolean;
  continuous_gps_opt_in: boolean;
  location_source: "gps" | "gps_corrected" | "manual";
}

interface FarmLocationPickerProps {
  value: FarmLocationValue;
  onChange: (next: FarmLocationValue) => void;
  allowAuthReverse?: boolean;
  compactMapHeight?: string;
}

const PIN_ICON = L.divIcon({
  className: "raitha-gps-pin",
  html: `<div style="width:26px;height:26px;border-radius:9999px;background:#176B35;border:3px solid #FFFFFF;box-shadow:0 3px 10px rgba(16,75,41,0.45);display:flex;align-items:center;justify-content:center;"><div style="width:8px;height:8px;border-radius:9999px;background:#FAF9F2;"></div></div>`,
  iconSize: [26, 26],
  iconAnchor: [13, 13],
});

export function FarmLocationPicker({
  value,
  onChange,
  allowAuthReverse = true,
  compactMapHeight = "h-56",
}: FarmLocationPickerProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const latestValueRef = useRef(value);
  latestValueRef.current = value;

  const {
    detecting,
    watching,
    error,
    lastFix,
    detectOnce,
    reverseLookup,
    startWatching,
    stopWatching,
    clearError,
  } = useLiveGps({
    initialContinuous: false,
    onDetected: ({ latitude, longitude, geocoded }) => {
      const curr = latestValueRef.current;
      onChange({
        ...curr,
        latitude,
        longitude,
        gps_consent: true,
        location_source: "gps",
        village: geocoded?.village || curr.village,
        taluk: geocoded?.taluk || curr.taluk,
        district: geocoded?.district || curr.district,
        state: geocoded?.state || curr.state,
        location_address: geocoded?.display_name || curr.location_address || `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`,
      });
    },
  });

  // Render or update interactive Leaflet map ONLY when verified user coordinates exist (never hardcoded city coordinates)
  useEffect(() => {
    const lat = value.latitude;
    const lon = value.longitude;

    if (lat == null || lon == null || !value.gps_consent) {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        markerRef.current = null;
      }
      return;
    }

    const container = mapContainerRef.current;
    if (!container) return;

    if (!mapInstanceRef.current) {
      const map = L.map(container, {
        center: [lat, lon],
        zoom: 14,
        zoomControl: true,
      });
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19,
      }).addTo(map);

      const marker = L.marker([lat, lon], { icon: PIN_ICON, draggable: true }).addTo(map);
      const applyManualPin = async (newLat: number, newLon: number) => {
        const roundedLat = Number(newLat.toFixed(6));
        const roundedLon = Number(newLon.toFixed(6));
        const geo = await reverseLookup(roundedLat, roundedLon, allowAuthReverse);
        const curr = latestValueRef.current;
        onChange({
          ...curr,
          latitude: roundedLat,
          longitude: roundedLon,
          gps_consent: true,
          location_source: "gps_corrected",
          village: geo?.village || curr.village,
          taluk: geo?.taluk || curr.taluk,
          district: geo?.district || curr.district,
          state: geo?.state || curr.state,
          location_address: geo?.display_name || `${roundedLat.toFixed(5)}, ${roundedLon.toFixed(5)}`,
        });
      };

      marker.on("dragend", () => {
        const pos = marker.getLatLng();
        void applyManualPin(pos.lat, pos.lng);
      });
      map.on("click", (evt: L.LeafletMouseEvent) => {
        marker.setLatLng(evt.latlng);
        void applyManualPin(evt.latlng.lat, evt.latlng.lng);
      });

      mapInstanceRef.current = map;
      markerRef.current = marker;
    } else {
      mapInstanceRef.current.setView([lat, lon], Math.max(mapInstanceRef.current.getZoom(), 13), {
        animate: true,
      });
      markerRef.current?.setLatLng([lat, lon]);
    }
  }, [value.latitude, value.longitude, value.gps_consent, allowAuthReverse, onChange, reverseLookup]);

  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
      stopWatching();
    };
  }, [stopWatching]);

  const handleDetectClick = async () => {
    clearError();
    onChange({ ...value, gps_consent: true });
    await detectOnce(allowAuthReverse);
  };

  const handleToggleContinuous = () => {
    if (watching) {
      stopWatching();
      onChange({ ...value, continuous_gps_opt_in: false });
    } else {
      onChange({ ...value, gps_consent: true, continuous_gps_opt_in: true });
      startWatching(allowAuthReverse);
    }
  };

  const handleDisableGps = () => {
    stopWatching();
    clearError();
    onChange({
      ...value,
      gps_consent: false,
      continuous_gps_opt_in: false,
      latitude: null,
      longitude: null,
      location_source: "manual",
    });
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-[#DCE8D8] bg-[#FAF9F2] p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <span className="h-9 w-9 rounded-lg bg-[#176B35] text-white flex items-center justify-center shrink-0">
              <LocateFixed className="w-5 h-5" />
            </span>
            <div>
              <h4 className="text-sm font-semibold text-[#202820]">Live Farm GPS & Location Map</h4>
              <p className="text-xs text-[#718071]">
                Uses device GPS only with your permission. Click GPS or enter Village/Taluk/District manually.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={handleDetectClick}
              disabled={detecting}
              className="rm-btn-primary !py-2 !px-3.5 text-xs flex items-center gap-1.5"
            >
              {detecting ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Detecting GPS...
                </>
              ) : value.latitude != null ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5" />
                  Refresh Location
                </>
              ) : (
                <>
                  <Navigation className="w-3.5 h-3.5" />
                  Detect My GPS
                </>
              )}
            </button>

            {value.gps_consent && (
              <button
                type="button"
                onClick={handleToggleContinuous}
                className={`px-3 py-2 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition ${
                  watching
                    ? "bg-[#FCECEC] text-[#D9534F] border-[#F5C6C5]"
                    : "bg-white text-[#104B29] border-[#DCE8D8] hover:bg-[#EDF5E9]"
                }`}
              >
                {watching ? (
                  <>
                    <Square className="w-3 h-3 fill-current" />
                    Stop Live Tracking
                  </>
                ) : (
                  <>
                    <LocateFixed className="w-3.5 h-3.5" />
                    Auto-Track (Opt-in)
                  </>
                )}
              </button>
            )}

            {value.gps_consent && (
              <button
                type="button"
                onClick={handleDisableGps}
                className="px-2.5 py-2 rounded-lg text-xs text-[#718071] hover:text-[#D9534F] border border-transparent hover:border-[#F5C6C5]"
              >
                Clear GPS
              </button>
            )}
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-2 rounded-lg bg-[#FCECEC] border border-[#F5C6C5] px-3 py-2.5 text-xs text-[#B23B37]">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">{error}</p>
              <p className="text-[11px] mt-0.5 text-[#718071]">
                Manual location fields below always remain available.
              </p>
            </div>
          </div>
        )}

        {value.latitude != null && value.longitude != null && value.gps_consent ? (
          <div className="space-y-2.5">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs bg-[#EDF5E9] border border-[#CFE4C8] rounded-lg px-3 py-2">
              <div className="flex items-center gap-1.5 text-[#104B29] font-medium">
                <CheckCircle2 className="w-4 h-4 text-[#176B35]" />
                <span>
                  GPS: {value.latitude.toFixed(5)}, {value.longitude.toFixed(5)}
                  {lastFix?.accuracyMeters ? ` (±${lastFix.accuracyMeters}m)` : ""}
                </span>
              </div>
              <span className="text-[11px] text-[#718071]">
                Source: {value.location_source === "gps_corrected" ? "Map Pin Corrected" : "Device GPS"} • Drag pin or tap map to adjust
              </span>
            </div>

            {value.location_address && (
              <div className="flex items-start gap-2 text-xs text-[#202820] bg-white border border-[#E6EBE2] rounded-lg px-3 py-2">
                <MapPin className="w-4 h-4 text-[#176B35] shrink-0 mt-0.5" />
                <span>{value.location_address}</span>
              </div>
            )}

            <div
              ref={mapContainerRef}
              className={`w-full ${compactMapHeight} rounded-xl border border-[#DCE8D8] overflow-hidden z-0`}
            />
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-[#CFE4C8] bg-white px-4 py-4 text-center text-xs text-[#718071]">
            Click <span className="font-semibold text-[#176B35]">Detect My GPS</span> to pinpoint your field on the map, or type your Village, Taluk, District, and State below.
          </div>
        )}
      </div>

      {/* Structured Village / Taluk / District / State Fields (GPS-filled + Always Editable) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div>
          <label className="block text-xs font-medium text-[#718071] mb-1">Village / Town</label>
          <input
            className="rm-input"
            value={value.village}
            placeholder="e.g., Kirugavalu"
            onChange={(e) =>
              onChange({
                ...value,
                village: e.target.value,
                location_source: value.latitude != null ? "gps_corrected" : "manual",
              })
            }
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-[#718071] mb-1">Taluk / Sub-district</label>
          <input
            className="rm-input"
            value={value.taluk}
            placeholder="e.g., Malavalli"
            onChange={(e) =>
              onChange({
                ...value,
                taluk: e.target.value,
                location_source: value.latitude != null ? "gps_corrected" : "manual",
              })
            }
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-[#718071] mb-1">District *</label>
          <input
            className="rm-input"
            value={value.district}
            required
            placeholder="e.g., Mandya"
            onChange={(e) =>
              onChange({
                ...value,
                district: e.target.value,
                location_source: value.latitude != null ? "gps_corrected" : "manual",
              })
            }
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-[#718071] mb-1">State *</label>
          <input
            className="rm-input"
            value={value.state}
            required
            placeholder="e.g., Karnataka"
            onChange={(e) =>
              onChange({
                ...value,
                state: e.target.value,
                location_source: value.latitude != null ? "gps_corrected" : "manual",
              })
            }
          />
        </div>
      </div>
    </div>
  );
}

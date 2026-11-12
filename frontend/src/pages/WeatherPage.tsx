import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { CloudRain, AlertTriangle, Waves, RefreshCw } from "lucide-react";
import {
  CardSkeleton,
  EmptyState,
  ErrorState,
  IntegrationStatusBadge,
} from "@/components/common/StateFeedback";
import { useAuth } from "@/context/AuthContext";
import { useAsyncState } from "@/hooks/useAsyncState";
import { api } from "@/services/api";
import type { WeatherFloodResponse } from "@/types";

export const WeatherPage: React.FC = () => {
  const { farmer } = useAuth();
  const [stateInput, setStateInput] = useState(farmer?.state || "Karnataka");
  const [districtInput, setDistrictInput] = useState(farmer?.district || "");
  const { data, loading, error, run } = useAsyncState<WeatherFloodResponse>();

  const loadWeather = () => {
    void run(() =>
      api.getWeather({
        state: stateInput,
        district: districtInput,
        lat: farmer?.gps_consent && farmer.latitude ? farmer.latitude : undefined,
        lon: farmer?.gps_consent && farmer.longitude ? farmer.longitude : undefined,
      })
    );
  };

  useEffect(() => {
    loadWeather();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-deep">Weather & Flood Watch</h1>
          <p className="text-sm text-muted mt-1">
            IMD is primary for official warnings, OpenWeather is fallback for forecasts only, and CWC covers flood gauges.
          </p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            loadWeather();
          }}
          className="flex flex-wrap items-center gap-2"
        >
          <input
            className="rm-input w-36"
            value={stateInput}
            onChange={(e) => setStateInput(e.target.value)}
            placeholder="State"
          />
          <input
            className="rm-input w-40"
            value={districtInput}
            onChange={(e) => setDistrictInput(e.target.value)}
            placeholder="District"
          />
          <button type="submit" className="rm-btn-primary">
            <RefreshCw className="h-4 w-4" />
            Check
          </button>
        </form>
      </div>

      {loading && !data ? (
        <div className="space-y-4">
          <CardSkeleton lines={3} />
          <CardSkeleton lines={5} />
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={loadWeather} />
      ) : !data ? (
        <EmptyState title="No weather data loaded" description="Select a state and district to inspect official sources." />
      ) : (
        <>
          <div className="rm-card p-4 flex flex-wrap items-center justify-between gap-3 text-xs">
            <span className="font-semibold text-deep">Location: {data.location_label}</span>
            <span className="text-muted">Freshness: {data.freshness_label}</span>
          </div>

          {/* IMD Warnings + CWC Flood */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rm-card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-deep flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-warning" />
                  IMD Official Weather Warnings
                </h2>
                <IntegrationStatusBadge status={data.imd_status} />
              </div>
              <p className="text-xs text-muted">{data.imd_source_note}</p>
              {data.warnings.length > 0 ? (
                <div className="space-y-2.5">
                  {data.warnings.map((w, idx) => (
                    <div key={idx} className="rounded-xl border border-[#176B35]/15 bg-mint/60 p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-ink">{w.title}</span>
                        <span className="text-xs font-semibold uppercase text-forest">{w.severity}</span>
                      </div>
                      <p className="text-xs text-muted mt-1">{w.description}</p>
                      <p className="text-[11px] text-muted mt-1">Source: {w.source}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl bg-cream p-4 text-xs text-muted">
                  No warnings returned. Raitha Mitra never fabricates synthetic weather alerts.
                </div>
              )}
            </div>

            <div className="rm-card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-deep flex items-center gap-2">
                  <Waves className="h-4 w-4 text-forest" />
                  CWC Flood Advisory
                </h2>
                <IntegrationStatusBadge status={data.flood_status} />
              </div>
              <p className="text-xs text-muted">{data.flood_source_note}</p>
              {data.flood_advisories.length > 0 ? (
                <div className="space-y-2">
                  {data.flood_advisories.map((f, idx) => (
                    <div key={idx} className="rounded-xl bg-mint/60 p-3 text-xs">
                      <p className="font-semibold text-ink">
                        {f.station} ({f.river})
                      </p>
                      <p className="text-muted mt-0.5">
                        Level: {f.level_m ?? "—"} m / Danger: {f.danger_level_m ?? "—"} m • {f.status}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl bg-cream p-4 text-xs text-muted">
                  Official CWC flood station portal:{" "}
                  <a
                    href="https://ffs.india-water.gov.in/"
                    target="_blank"
                    rel="noreferrer"
                    className="font-semibold text-forest underline"
                  >
                    ffs.india-water.gov.in
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Forecast Section */}
          <div className="rm-card p-5 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 className="text-base font-bold text-deep flex items-center gap-2">
                  <CloudRain className="h-4 w-4 text-forest" />
                  Temperature & Rainfall Forecast
                </h2>
                <p className="text-xs text-muted mt-0.5">Source: {data.forecast_source}</p>
              </div>
              <IntegrationStatusBadge status={data.forecast_status} />
            </div>

            {data.forecast.length > 0 ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.forecast}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#DCE8D5" />
                    <XAxis dataKey="timestamp" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="temp_c"
                      name="Temp (°C)"
                      stroke="#176B35"
                      fill="#EDF5E9"
                    />
                    <Area
                      type="monotone"
                      dataKey="rain_mm"
                      name="Rain (mm)"
                      stroke="#56A832"
                      fill="#56A832"
                      fillOpacity={0.2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyState
                title="Forecast feed not configured"
                description="Add OPENWEATHER_API_KEY (or IMD credentials) in backend/.env to display live temperature and rainfall forecast charts."
              />
            )}
          </div>
        </>
      )}
    </div>
  );
};

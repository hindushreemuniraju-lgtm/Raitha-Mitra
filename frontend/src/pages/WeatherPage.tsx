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
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-deep">Location: {data.location_label}</span>
            {data.latitude != null && data.longitude != null && (
              <span className="rounded-full bg-mint px-2.5 py-0.5 text-[11px] font-medium text-forest">
                GPS {data.latitude.toFixed(4)}, {data.longitude.toFixed(4)}
              </span>
            )}
          </div>
          <span className="text-muted">Freshness: {data.freshness_label}</span>
        </div>

        {/* Classified Alerts (Explicit separation: Official Flood vs Heavy Rain vs Waterlogging Estimate) */}
        {data.classified_alerts && data.classified_alerts.length > 0 && (
          <div className="space-y-2.5">
            <h2 className="text-base font-bold text-deep">Classified Weather & Flood Risk Breakdown</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {data.classified_alerts.map((alert, idx) => {
                const isOfficialFlood = alert.alert_type === "official_flood_warning";
                const isHeavyRain = alert.alert_type === "heavy_rainfall_warning";
                const tone = isOfficialFlood
                  ? "border-danger/40 bg-[#FCECEC]"
                  : isHeavyRain
                  ? "border-warning/50 bg-[#FEF6E6]"
                  : "border-[#176B35]/20 bg-mint/60";
                return (
                  <div key={idx} className={`rounded-2xl border p-4 space-y-1.5 ${tone}`}>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[11px] font-bold uppercase tracking-wide text-deep">
                        {alert.alert_type.replace(/_/g, " ")}
                      </span>
                      <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold text-ink border border-black/10">
                        {alert.is_official ? "Official Source" : "Forecast / Model"}
                      </span>
                    </div>
                    <p className="text-sm font-bold text-ink">{alert.title_en}</p>
                    <p className="text-xs text-ink/90">{alert.message_en}</p>
                    <p className="text-xs font-medium text-deep">{alert.message_kn}</p>
                    <p className="text-[11px] text-muted">Source: {alert.source}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

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
                description="Live weather forecast could not be loaded for this location right now."
              />
            )}

            {/* 7-Day Daily Rainfall & Intensity Cards */}
            {data.daily_forecast && data.daily_forecast.length > 0 && (
              <div className="pt-3 border-t border-[#176B35]/10 space-y-2.5">
                <h3 className="text-sm font-bold text-deep">7-Day Rainfall, Wind & Intensity Outlook</h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
                  {data.daily_forecast.map((d) => {
                    const heavy = d.rain_intensity === "heavy" || d.rain_intensity === "very_heavy";
                    return (
                      <div
                        key={d.date}
                        className={`rounded-xl border p-3 text-xs space-y-1 ${
                          heavy
                            ? "border-warning/60 bg-[#FEF6E6]"
                            : "border-[#176B35]/15 bg-cream"
                        }`}
                      >
                        <p className="font-bold text-deep">{d.date}</p>
                        <p className="text-[11px] text-muted capitalize">{d.condition}</p>
                        <p className="font-semibold text-ink">
                          {d.temp_min_c}° – {d.temp_max_c}°C
                        </p>
                        <p className={`font-bold ${heavy ? "text-[#B27700]" : "text-forest"}`}>
                          {d.rain_sum_mm} mm ({d.rain_probability_pct}%)
                        </p>
                        <p className="text-[10px] uppercase font-semibold text-muted">
                          {d.rain_intensity.replace("_", " ")} • Wind {d.wind_max_kmh} km/h
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

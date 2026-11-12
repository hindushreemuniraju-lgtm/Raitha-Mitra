import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Mic,
  TestTube2,
  Bug,
  CloudRain,
  Store,
  Calculator,
  Sprout,
  Landmark,
  AlertTriangle,
  TrendingUp,
  Bell,
  ShieldAlert,
  MapPin,
} from "lucide-react";
import { AnimatedCounter } from "@/components/common/AnimatedCounter";
import { MediaPreview } from "@/components/common/MediaPreview";
import {
  CardSkeleton,
  EmptyState,
  ErrorState,
  IntegrationStatusBadge,
} from "@/components/common/StateFeedback";
import { useAsyncState } from "@/hooks/useAsyncState";
import { api } from "@/services/api";
import type { DashboardSummary } from "@/types";

const QUICK_ACTIONS = [
  { to: "/voice", label: "Ask Raitha Mitra", icon: Mic, primary: true },
  { to: "/soil", label: "Analyze Soil", icon: TestTube2 },
  { to: "/pest-detection", label: "Detect Disease", icon: Bug },
  { to: "/weather", label: "Check Weather", icon: CloudRain },
  { to: "/mandi", label: "Find Prices", icon: Store },
  { to: "/profit", label: "Calculate Profit", icon: Calculator },
];

export const DashboardPage: React.FC = () => {
  const { data, loading, error, run } = useAsyncState<DashboardSummary>();

  useEffect(() => {
    void run(() => api.getDashboard());
  }, [run]);

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <CardSkeleton lines={2} />
          <CardSkeleton lines={2} />
          <CardSkeleton lines={2} />
          <CardSkeleton lines={2} />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CardSkeleton lines={5} />
          <CardSkeleton lines={5} />
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => void run(() => api.getDashboard())} />;
  }

  if (!data) {
    return (
      <EmptyState
        title="No dashboard data yet"
        description="Complete your farm profile or add soil and crop records to view insights."
      />
    );
  }

  const latestForecast = data.weather.forecast[0];

  return (
    <div className="space-y-6">
      {/* Greeting + Quick Actions */}
      <div className="rm-card p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          {data.farmer.avatar_url && (
            <img
              src={data.farmer.avatar_url}
              alt={data.farmer.full_name}
              className="h-14 w-14 rounded-2xl object-cover border border-forest/20 shrink-0"
            />
          )}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-forest flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5" />
              {[data.farmer.village, data.farmer.taluk, data.farmer.district || data.farmer.state]
                .filter(Boolean)
                .join(", ")}{" "}
              • {data.farmer.farm_size_acres} Acres
            </p>
            <h1 className="text-2xl font-bold text-deep mt-1">
              Namaste, {data.farmer.full_name}
            </h1>
            <p className="text-sm text-muted mt-1">
              Main crops:{" "}
              {data.farmer.main_crops.length > 0
                ? data.farmer.main_crops.join(", ")
                : "Not specified yet"}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {QUICK_ACTIONS.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.to}
                to={action.to}
                className={action.primary ? "rm-btn-primary" : "rm-btn-secondary"}
              >
                <Icon className="h-4 w-4" />
                <span>{action.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Top KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rm-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted">Weather & Alerts</span>
            <IntegrationStatusBadge status={data.weather.forecast_status} />
          </div>
          {latestForecast ? (
            <>
              <p className="text-2xl font-bold text-deep">
                <AnimatedCounter value={latestForecast.temp_c} decimals={1} suffix=" °C" />
              </p>
              <p className="text-xs text-muted">
                {latestForecast.condition} • Humidity {latestForecast.humidity_pct}%
              </p>
            </>
          ) : (
            <p className="text-sm text-muted">
              Weather feed not configured. Add IMD or OpenWeather key in backend `.env`.
            </p>
          )}
        </div>

        <div className="rm-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted">Latest Soil Health</span>
            <TestTube2 className="h-4 w-4 text-forest" />
          </div>
          {data.latest_soil ? (
            <>
              <p className="text-2xl font-bold text-deep">
                pH {data.latest_soil.ph !== null && data.latest_soil.ph !== undefined ? data.latest_soil.ph.toFixed(1) : "—"}
              </p>
              <p className="text-xs text-muted">
                {data.latest_soil.source_type === "dataset_estimate"
                  ? `Estimated (${data.latest_soil.confidence_level})`
                  : `Verified ${data.latest_soil.source_type.replace("_", " ")}`}
              </p>
            </>
          ) : (
            <Link to="/soil" className="text-sm font-semibold text-forest hover:underline block">
              Upload Soil Health Card →
            </Link>
          )}
        </div>

        <div className="rm-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted">Expected Yield</span>
            <TrendingUp className="h-4 w-4 text-forest" />
          </div>
          {data.yield_preview ? (
            <>
              <p className="text-2xl font-bold text-deep">
                <AnimatedCounter
                  value={data.yield_preview.yield_expected_qtl_total}
                  decimals={1}
                  suffix=" qtl"
                />
              </p>
              <p className="text-xs text-muted">
                {data.yield_preview.crop_name} ({data.yield_preview.confidence_label} confidence)
              </p>
            </>
          ) : (
            <Link to="/growth" className="text-sm font-semibold text-forest hover:underline block">
              Track a sown crop →
            </Link>
          )}
        </div>

        <div className="rm-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted">Estimated Profit</span>
            <Calculator className="h-4 w-4 text-forest" />
          </div>
          {data.latest_profit ? (
            <>
              <p className="text-2xl font-bold text-deep">
                ₹<AnimatedCounter value={data.latest_profit.net_profit} />
              </p>
              <p className="text-xs text-muted">
                {data.latest_profit.crop_name} • Margin {data.latest_profit.margin_pct.toFixed(1)}% (Editable)
              </p>
            </>
          ) : (
            <Link to="/profit" className="text-sm font-semibold text-forest hover:underline block">
              Run profit estimate →
            </Link>
          )}
        </div>
      </div>

      {/* Harvest Protection & Active Alerts Highlight Row */}
      {((data.harvest_protection?.decisions?.length || 0) > 0 || (data.unread_notifications_count || 0) > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {data.harvest_protection && data.harvest_protection.decisions.length > 0 && (
            <div className="rm-card p-5 space-y-2.5 border-l-4 border-l-forest">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-deep flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-forest" />
                  Harvest Protection Intelligence
                </h2>
                <Link to="/harvest" className="text-xs font-semibold text-forest hover:underline">
                  Full Advisor →
                </Link>
              </div>
              {data.harvest_protection.decisions.slice(0, 2).map((dec, idx) => (
                <div key={dec.crop_id ?? idx} className="rounded-xl bg-[#FAF9F2] border border-[#176B35]/10 p-3 text-xs space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-bold text-deep">{dec.crop_name}</span>
                    <span className="rounded-full bg-mint px-2.5 py-0.5 text-[10px] font-bold text-forest">
                      {dec.action_label_en}
                    </span>
                  </div>
                  <p className="text-ink">{dec.headline_en}</p>
                  <p className="text-deep/85">{dec.headline_kn}</p>
                </div>
              ))}
            </div>
          )}

          <div className="rm-card p-5 space-y-2.5">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-deep flex items-center gap-2">
                <Bell className="h-4 w-4 text-forest" />
                Smart Farm Alerts ({data.unread_notifications_count || 0} unread)
              </h2>
              <Link to="/notifications" className="text-xs font-semibold text-forest hover:underline">
                Open Alert Center →
              </Link>
            </div>
            {data.recent_notifications && data.recent_notifications.length > 0 ? (
              <div className="space-y-2">
                {data.recent_notifications.slice(0, 2).map((n) => (
                  <div key={n.id} className="rounded-xl bg-cream border border-[#176B35]/10 p-3 text-xs space-y-0.5">
                    <p className="font-bold text-deep">{n.title_kn}</p>
                    <p className="text-muted">{n.title_en}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted">
                Open the Alert Center to scan live rainfall, official flood warnings, and crop harvest windows for your farm GPS.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Middle Grid: Weather Warnings + Crop Stage + Pest Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alerts */}
        <div className="rm-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-deep flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-warning" />
              IMD & Flood Alerts
            </h2>
            <Link to="/weather" className="text-xs font-semibold text-forest hover:underline">
              Details
            </Link>
          </div>
          {data.weather.warnings.length > 0 ? (
            <div className="space-y-2">
              {data.weather.warnings.map((w, i) => (
                <div key={i} className="rounded-xl bg-mint p-3 text-xs">
                  <p className="font-semibold text-deep">{w.title}</p>
                  <p className="text-muted mt-0.5">{w.description}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted leading-relaxed">
              {data.weather.imd_source_note}
            </p>
          )}
          <p className="text-[11px] text-muted pt-1">{data.weather.flood_source_note}</p>
        </div>

        {/* Active Crop Stage */}
        <div className="rm-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-deep flex items-center gap-2">
              <Sprout className="h-4 w-4 text-forest" />
              Crop Growth Stage
            </h2>
            <Link to="/growth" className="text-xs font-semibold text-forest hover:underline">
              Manage
            </Link>
          </div>
          {data.active_crops.length > 0 ? (
            <div className="space-y-2.5">
              {data.active_crops.slice(0, 3).map((crop) => (
                <div key={crop.id} className="rounded-xl bg-cream border border-[#176B35]/10 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-ink">{crop.crop_name}</span>
                    <span className="text-xs font-medium text-forest capitalize">
                      {crop.current_stage.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-xs text-muted mt-1">
                    Day {crop.days_since_sowing} • {crop.acreage} acres • {crop.irrigation_type}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted">
              No active crops tracked yet. Add a sown crop to unlock daily stage checklists.
            </p>
          )}
        </div>

        {/* Recent Pest Scans */}
        <div className="rm-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-deep flex items-center gap-2">
              <Bug className="h-4 w-4 text-forest" />
              Recent Pest & Disease Scans
            </h2>
            <Link to="/pest-detection" className="text-xs font-semibold text-forest hover:underline">
              Scan Photo
            </Link>
          </div>
          {data.recent_scans.length > 0 ? (
            <div className="space-y-2.5">
              {data.recent_scans.slice(0, 3).map((scan) => (
                <div key={scan.id} className="rounded-xl bg-cream border border-[#176B35]/10 p-3 space-y-2">
                  {scan.image_url && (
                    <MediaPreview
                      url={scan.image_url}
                      filename={scan.original_filename || `${scan.crop_name || "Leaf"} Scan`}
                      mimeType={scan.file_mime_type}
                      kind="image"
                      compact
                    />
                  )}
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-semibold text-ink">
                      {scan.diagnosis_name || scan.status.replace("_", " ")}
                    </span>
                    <IntegrationStatusBadge
                      status={scan.status === "diagnosed" ? "configured" : "not_configured"}
                      label={scan.status}
                    />
                  </div>
                  <p className="text-xs text-muted mt-1">
                    Crop: {scan.crop_name || "Auto"} • Adapter: {scan.adapter_used}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted">
              No leaf scans yet. Upload a clear crop image when inspecting symptoms.
            </p>
          )}
        </div>
      </div>

      {/* Bottom Grid: Mandi Summary + Scheme Suggestions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rm-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-deep flex items-center gap-2">
              <Store className="h-4 w-4 text-forest" />
              Mandi Price Summary
            </h2>
            <Link to="/mandi" className="text-xs font-semibold text-forest hover:underline">
              Open Mandi Explorer
            </Link>
          </div>
          {data.mandi_preview.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-muted border-b border-[#176B35]/10">
                    <th className="py-2">Commodity</th>
                    <th className="py-2">Market</th>
                    <th className="py-2">Modal ₹/qtl</th>
                  </tr>
                </thead>
                <tbody>
                  {data.mandi_preview.slice(0, 4).map((row, idx) => (
                    <tr key={idx} className="border-b border-[#176B35]/5">
                      <td className="py-2 font-semibold text-ink">{row.commodity}</td>
                      <td className="py-2 text-muted">{row.market}</td>
                      <td className="py-2 font-bold text-forest">₹{row.modal_price_inr}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-muted">
              Live AGMARKNET / CEDA API keys are not configured. Visit Mandi Prices to view source status or inspect labelled demo data.
            </p>
          )}
        </div>

        <div className="rm-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-deep flex items-center gap-2">
              <Landmark className="h-4 w-4 text-forest" />
              Suggested Government Schemes
            </h2>
            <Link to="/schemes" className="text-xs font-semibold text-forest hover:underline">
              View All
            </Link>
          </div>
          <div className="space-y-2.5">
            {data.suggested_schemes.slice(0, 3).map((scheme) => (
              <div key={scheme.id} className="rounded-xl bg-mint/60 p-3 flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-deep">{scheme.name}</p>
                  <p className="text-xs text-muted mt-0.5 line-clamp-2">{scheme.benefits}</p>
                </div>
                <a
                  href={scheme.official_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs font-semibold text-forest hover:underline shrink-0"
                >
                  Official Site
                </a>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

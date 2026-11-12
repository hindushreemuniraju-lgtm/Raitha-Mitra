import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  CloudRain,
  IndianRupee,
  RefreshCw,
  ShieldAlert,
  Sprout,
} from "lucide-react";
import {
  CardSkeleton,
  EmptyState,
  ErrorState,
} from "@/components/common/StateFeedback";
import { useLanguage } from "@/context/LanguageContext";
import { api } from "@/services/api";
import type { HarvestProtectionDecision, HarvestProtectionSummary } from "@/types";

export const HarvestProtectionPage: React.FC = () => {
  const { language } = useLanguage();
  const isKn = language === "kn-IN";

  const [summary, setSummary] = useState<HarvestProtectionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // What-If Custom Crop Analyzer
  const [cropName, setCropName] = useState("Tomato");
  const [sowingDate, setSowingDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 80);
    return d.toISOString().slice(0, 10);
  });
  const [stage, setStage] = useState("maturity");
  const [acreage, setAcreage] = useState("1.5");
  const [irrigation, setIrrigation] = useState("drip");
  const [analyzing, setAnalyzing] = useState(false);
  const [customResult, setCustomResult] = useState<HarvestProtectionDecision | null>(null);

  const loadProtection = () => {
    setLoading(true);
    setError(null);
    api
      .getHarvestProtection()
      .then(setSummary)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load harvest protection"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProtection();
  }, []);

  const handleAnalyzeCustom = async (e: React.FormEvent) => {
    e.preventDefault();
    setAnalyzing(true);
    setError(null);
    try {
      const res = await api.analyzeHarvest({
        crop_name: cropName,
        sowing_date: sowingDate,
        current_stage: stage,
        acreage: Number(acreage) || 1,
        irrigation_type: irrigation,
      });
      setCustomResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  const renderActionBadge = (dec: HarvestProtectionDecision) => {
    const label = isKn ? dec.action_label_kn : dec.action_label_en;
    if (dec.action === "harvest_now") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-[#FCECEC] text-[#D9534F] border border-[#F5C6C5] px-3 py-1 text-xs font-bold">
          <AlertTriangle className="h-3.5 w-3.5" />
          {label}
        </span>
      );
    }
    if (dec.action === "wait_for_maturity" || dec.action === "protect_crop") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-[#FEF6E6] text-[#946200] border border-[#F5DAA0] px-3 py-1 text-xs font-bold">
          <ShieldAlert className="h-3.5 w-3.5" />
          {label}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-[#EDF5E9] text-[#176B35] border border-[#CFE4C8] px-3 py-1 text-xs font-bold">
        <CheckCircle2 className="h-3.5 w-3.5" />
        {label}
      </span>
    );
  };

  const renderDecisionCard = (dec: HarvestProtectionDecision, idx: number) => (
    <div key={dec.crop_id ?? `custom-${idx}`} className="rm-card p-6 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Sprout className="h-5 w-5 text-forest" />
            <h3 className="text-lg font-bold text-deep">
              {dec.crop_name} {dec.variety ? `(${dec.variety})` : ""}
            </h3>
          </div>
          <p className="text-xs text-muted mt-1">
            Stage: <strong className="capitalize text-ink">{dec.current_stage}</strong> • Age {dec.crop_age_days} days • Maturity{" "}
            {dec.expected_maturity_date} ({dec.days_remaining_to_maturity} days remaining)
          </p>
        </div>
        {renderActionBadge(dec)}
      </div>

      {/* Weather Metrics Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
        <div className="rounded-xl bg-cream p-3 border border-[#176B35]/10">
          <span className="text-muted flex items-center gap-1">
            <CloudRain className="h-3.5 w-3.5 text-forest" /> 24h Rain
          </span>
          <p className="font-bold text-deep mt-0.5">{dec.rain_24h_mm} mm</p>
        </div>
        <div className="rounded-xl bg-cream p-3 border border-[#176B35]/10">
          <span className="text-muted">72h Rain Outlook</span>
          <p className="font-bold text-deep mt-0.5">
            {dec.rain_72h_mm} mm ({dec.max_rain_probability_pct}%)
          </p>
        </div>
        <div className="rounded-xl bg-cream p-3 border border-[#176B35]/10">
          <span className="text-muted">Max Wind</span>
          <p className="font-bold text-deep mt-0.5">{dec.max_wind_kmh} km/h</p>
        </div>
        <div className="rounded-xl bg-cream p-3 border border-[#176B35]/10">
          <span className="text-muted flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5 text-forest" /> Readiness
          </span>
          <p className="font-bold text-deep capitalize mt-0.5">{dec.readiness_status.replace(/_/g, " ")}</p>
        </div>
      </div>

      {/* Main Decision Bilingual */}
      <div className="rounded-2xl bg-[#EDF5E9] border border-[#CFE4C8] p-4 space-y-1.5">
        <p className="text-sm font-bold text-deep">{isKn ? dec.headline_kn : dec.headline_en}</p>
        <p className="text-xs text-ink leading-relaxed">{isKn ? dec.explanation_kn : dec.explanation_en}</p>
        <p className="text-xs text-deep/85 pt-1 border-t border-[#176B35]/10">
          {isKn ? dec.explanation_en : dec.explanation_kn}
        </p>
      </div>

      {/* Precautions + Profit Optimization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 text-xs">
        <div className="rounded-2xl bg-cream border border-[#176B35]/10 p-4 space-y-2">
          <p className="font-bold text-deep">Crop-Specific Precautions & Notes</p>
          <ul className="list-disc pl-4 space-y-1 text-ink">
            {(isKn ? dec.precautions_kn : dec.precautions_en).map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
          {dec.crop_specific_notes.length > 0 && (
            <div className="pt-2 border-t border-[#176B35]/10 text-muted space-y-1">
              {dec.crop_specific_notes.map((n, i) => (
                <p key={i}>• {n}</p>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl bg-cream border border-[#176B35]/10 p-4 space-y-2">
          <div className="flex items-center justify-between gap-2">
            <p className="font-bold text-deep flex items-center gap-1.5">
              <IndianRupee className="h-3.5 w-3.5 text-forest" />
              Spoilage & Market Timing Optimization
            </p>
            <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold uppercase text-muted border border-[#DCE8D8]">
              Spoilage: {dec.profit_optimization.spoilage_risk_level}
            </span>
          </div>
          {dec.profit_optimization.current_modal_price_inr_qtl != null && (
            <p className="font-semibold text-forest">
              Live Mandi Modal: ₹{dec.profit_optimization.current_modal_price_inr_qtl}/qtl ({dec.profit_optimization.market_name})
            </p>
          )}
          <p className="text-ink leading-relaxed">
            {isKn ? dec.profit_optimization.explanation_kn : dec.profit_optimization.explanation_en}
          </p>
          <p className="text-muted">
            <strong>Transport:</strong> {dec.profit_optimization.transport_timing_advice}
          </p>
          <p className="text-[11px] text-muted italic">{dec.profit_optimization.honesty_note}</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-deep">Smart Harvest Protection & Profit Advisor</h1>
          <p className="text-sm text-muted mt-1">
            Combines your verified GPS weather forecast, crop growth stage & maturity window so ripe crops beat heavy rain while immature crops are never harvested early.
          </p>
        </div>
        <button type="button" onClick={loadProtection} className="rm-btn-secondary self-start sm:self-auto">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh Analysis
        </button>
      </div>

      {error && <ErrorState message={error} onRetry={loadProtection} />}

      {summary && (
        <div className="rm-card px-4 py-3 text-xs flex flex-wrap items-center justify-between gap-2">
          <span className="font-semibold text-deep">Farm Location: {summary.location_label}</span>
          <span className="text-muted">{summary.weather_freshness}</span>
        </div>
      )}

      {loading && !summary ? (
        <div className="space-y-4">
          <CardSkeleton lines={5} />
          <CardSkeleton lines={5} />
        </div>
      ) : summary && summary.decisions.length > 0 ? (
        <div className="space-y-5">{summary.decisions.map((d, i) => renderDecisionCard(d, i))}</div>
      ) : (
        <EmptyState
          title="No active tracked crops yet"
          description="Add your sown crops in Crop Growth Monitoring or run the custom crop simulator below."
        />
      )}

      {/* Custom Crop Harvest Simulator */}
      <form onSubmit={handleAnalyzeCustom} className="rm-card p-6 space-y-4">
        <h2 className="text-base font-bold text-deep">Simulate Harvest Decision for Any Crop</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
          <div>
            <label className="block text-xs font-semibold mb-1">Crop</label>
            <input className="rm-input" value={cropName} onChange={(e) => setCropName(e.target.value)} required />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Sowing Date</label>
            <input type="date" className="rm-input" value={sowingDate} onChange={(e) => setSowingDate(e.target.value)} required />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Current Stage</label>
            <select className="rm-input" value={stage} onChange={(e) => setStage(e.target.value)}>
              <option value="germination">Germination</option>
              <option value="vegetative">Vegetative</option>
              <option value="flowering">Flowering</option>
              <option value="fruiting">Fruiting / Pod Fill</option>
              <option value="maturity">Maturity / Harvest Ready</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Acreage & Irrigation</label>
            <div className="flex gap-2">
              <input type="number" step="0.1" min="0.1" className="rm-input w-20" value={acreage} onChange={(e) => setAcreage(e.target.value)} />
              <select className="rm-input" value={irrigation} onChange={(e) => setIrrigation(e.target.value)}>
                <option value="drip">Drip</option>
                <option value="furrow">Furrow</option>
                <option value="rainfed">Rainfed</option>
              </select>
            </div>
          </div>
          <button type="submit" disabled={analyzing} className="rm-btn-primary">
            {analyzing ? "Evaluating..." : "Analyze Crop"}
          </button>
        </div>
      </form>

      {customResult && renderDecisionCard(customResult, 999)}
    </div>
  );
};

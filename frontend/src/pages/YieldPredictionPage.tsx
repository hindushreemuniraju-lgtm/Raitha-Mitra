import React, { useState } from "react";
import { TrendingUp, Calendar, Info } from "lucide-react";
import {
  CardSkeleton,
  EmptyState,
  ErrorState,
  IntegrationStatusBadge,
} from "@/components/common/StateFeedback";
import { useAuth } from "@/context/AuthContext";
import { useAsyncState } from "@/hooks/useAsyncState";
import { api } from "@/services/api";
import type { YieldPredictionResponse } from "@/types";

export const YieldPredictionPage: React.FC = () => {
  const { farmer } = useAuth();
  const [cropName, setCropName] = useState(farmer?.main_crops?.[0] || "Ragi");
  const [sowingDate, setSowingDate] = useState("2026-07-15");
  const [acreage, setAcreage] = useState(String(farmer?.farm_size_acres || 2));
  const [irrigation, setIrrigation] = useState("drip");
  const [stage, setStage] = useState("flowering");
  const [pestStatus, setPestStatus] = useState("none");
  const [rainfall, setRainfall] = useState("normal");

  const { data, loading, error, run } = useAsyncState<YieldPredictionResponse>();

  const handlePredict = (e: React.FormEvent) => {
    e.preventDefault();
    void run(() =>
      api.predictYield({
        crop_name: cropName,
        sowing_date: sowingDate,
        acreage: Number(acreage) || 1,
        irrigation_type: irrigation,
        growth_stage: stage,
        pest_status: pestStatus,
        rainfall_adequacy: rainfall,
      })
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-deep">Yield & Harvest Window Prediction</h1>
        <p className="text-sm text-muted mt-1">
          Modular agronomic engine outputting yield range, confidence, and maturity-based harvest windows.
        </p>
      </div>

      <form onSubmit={handlePredict} className="rm-card p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 items-end">
        <div>
          <label className="block text-xs font-semibold mb-1">Crop *</label>
          <input className="rm-input" required value={cropName} onChange={(e) => setCropName(e.target.value)} />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Sowing Date *</label>
          <input type="date" className="rm-input" required value={sowingDate} onChange={(e) => setSowingDate(e.target.value)} />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Area (Acres)</label>
          <input type="number" step="0.1" min="0.1" className="rm-input" value={acreage} onChange={(e) => setAcreage(e.target.value)} />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Irrigation</label>
          <select className="rm-input" value={irrigation} onChange={(e) => setIrrigation(e.target.value)}>
            <option value="drip">Drip</option>
            <option value="sprinkler">Sprinkler</option>
            <option value="furrow">Furrow</option>
            <option value="rainfed">Rainfed</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Current Stage</label>
          <select className="rm-input" value={stage} onChange={(e) => setStage(e.target.value)}>
            <option value="germination">Germination</option>
            <option value="vegetative">Vegetative</option>
            <option value="flowering">Flowering</option>
            <option value="fruiting">Fruiting / Grain Fill</option>
            <option value="maturity">Maturity</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Pest / Disease Status</label>
          <select className="rm-input" value={pestStatus} onChange={(e) => setPestStatus(e.target.value)}>
            <option value="none">None / Controlled</option>
            <option value="moderate">Moderate Pressure</option>
            <option value="severe">Severe Infestation</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Season Rainfall</label>
          <select className="rm-input" value={rainfall} onChange={(e) => setRainfall(e.target.value)}>
            <option value="normal">Normal / Adequate</option>
            <option value="deficit">Deficit / Dry</option>
            <option value="excess">Excess / Waterlogging</option>
          </select>
        </div>
        <button type="submit" disabled={loading} className="rm-btn-primary">
          <TrendingUp className="h-4 w-4" />
          {loading ? "Computing..." : "Predict Yield"}
        </button>
      </form>

      {loading ? (
        <CardSkeleton lines={5} />
      ) : error ? (
        <ErrorState message={error} />
      ) : !data ? (
        <EmptyState
          title="Configure your crop parameters"
          description="Select crop, sowing date, irrigation, and pest status to compute an agronomic yield range and maturity harvest window."
        />
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rm-card p-5 space-y-1">
              <span className="text-xs font-semibold text-muted">Expected Total Yield ({data.acreage} ac)</span>
              <p className="text-3xl font-extrabold text-forest">{data.yield_expected_qtl_total} qtl</p>
              <p className="text-xs text-muted">
                Range: {data.yield_min_qtl_total} – {data.yield_max_qtl_total} qtl ({data.yield_per_acre_range_qtl})
              </p>
            </div>
            <div className="rm-card p-5 space-y-1">
              <span className="text-xs font-semibold text-muted">Model Confidence</span>
              <p className="text-3xl font-extrabold text-deep">{data.confidence_pct}%</p>
              <p className="text-xs text-muted">{data.confidence_label} confidence (tightens with lab soil data)</p>
            </div>
            <div className="rm-card p-5 space-y-1">
              <span className="text-xs font-semibold text-muted flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-forest" />
                Maturity Harvest Window
              </span>
              <p className="text-lg font-bold text-deep mt-1">
                {data.harvest_window_start} → {data.harvest_window_end}
              </p>
              <p className="text-xs text-muted">Anchored on physiological maturity & grain/fruit quality</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rm-card p-5 space-y-2">
              <h2 className="text-base font-bold text-deep">Maturity & Quality Indicators</h2>
              <ul className="list-disc pl-4 text-xs text-ink/90 space-y-1.5">
                {data.maturity_basis.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </div>

            <div className="rm-card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-deep">Risk Factors & Google ALU/AMED</h2>
                <IntegrationStatusBadge status={data.google_agri_status} />
              </div>
              <ul className="list-disc pl-4 text-xs text-ink/90 space-y-1">
                {data.risk_factors.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
              <div className="rounded-xl bg-cream p-3 text-xs text-muted flex items-start gap-2">
                <Info className="h-4 w-4 text-forest shrink-0 mt-0.5" />
                <span>{data.google_agri_note}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState } from "react";
import { FlaskConical } from "lucide-react";
import { CardSkeleton, EmptyState, ErrorState } from "@/components/common/StateFeedback";
import { useAuth } from "@/context/AuthContext";
import { useAsyncState } from "@/hooks/useAsyncState";
import { api } from "@/services/api";
import type { FertilizerResponse } from "@/types";

export const FertilizerPage: React.FC = () => {
  const { farmer } = useAuth();
  const [cropName, setCropName] = useState(farmer?.main_crops?.[0] || "Ragi");
  const [stage, setStage] = useState("basal");
  const [acres, setAcres] = useState(String(farmer?.farm_size_acres || 2));

  const { data, loading, error, run } = useAsyncState<FertilizerResponse>();

  const handleCalculate = (e: React.FormEvent) => {
    e.preventDefault();
    void run(() =>
      api.recommendFertilizer({
        crop_name: cropName,
        growth_stage: stage,
        farm_size_acres: Number(acres) || 1,
      })
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-deep">Fertilizer & Nutrient Planner</h1>
        <p className="text-sm text-muted mt-1">
          Calculates organic and chemical NPK doses scaled to your farm size and verified soil deficiencies. Prices are shown only from verified dated feeds.
        </p>
      </div>

      <form onSubmit={handleCalculate} className="rm-card p-5 grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
        <div>
          <label className="block text-xs font-semibold mb-1">Crop Name *</label>
          <input
            required
            className="rm-input"
            value={cropName}
            onChange={(e) => setCropName(e.target.value)}
            placeholder="e.g. Tomato, Paddy, Ragi"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Growth Stage</label>
          <select className="rm-input" value={stage} onChange={(e) => setStage(e.target.value)}>
            <option value="basal">Basal / Sowing</option>
            <option value="vegetative">Vegetative</option>
            <option value="flowering">Flowering</option>
            <option value="fruiting">Fruiting / Grain Fill</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Area (Acres)</label>
          <input
            type="number"
            step="0.1"
            min="0.1"
            className="rm-input"
            value={acres}
            onChange={(e) => setAcres(e.target.value)}
          />
        </div>
        <button type="submit" disabled={loading} className="rm-btn-primary">
          <FlaskConical className="h-4 w-4" />
          {loading ? "Calculating..." : "Generate Plan"}
        </button>
      </form>

      {loading ? (
        <CardSkeleton lines={5} />
      ) : error ? (
        <ErrorState message={error} />
      ) : !data ? (
        <EmptyState
          title="Enter crop and stage to calculate nutrients"
          description="Raitha Mitra automatically applies your verified Soil Health Card values if uploaded."
        />
      ) : (
        <div className="space-y-4">
          <div className="rm-surface p-4 text-xs space-y-1">
            <p>
              <strong>Soil Basis:</strong> {data.soil_basis}
            </p>
            {data.deficiencies_detected.length > 0 && (
              <p className="text-deep">
                <strong>Deficiencies Addressed:</strong> {data.deficiencies_detected.join(" • ")}
              </p>
            )}
            {data.missing_soil_parameters.length > 0 && (
              <p className="text-[#8A5B00]">
                <strong>Untested / Missing Parameters:</strong> {data.missing_soil_parameters.join(", ")}
              </p>
            )}
            <p className="text-muted">{data.price_notice}</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[
              { title: "Organic Amendments", items: data.organic_plan },
              { title: "Chemical & Micronutrient Plan", items: data.chemical_plan },
            ].map((section) => (
              <div key={section.title} className="rm-card p-5 space-y-3">
                <h2 className="text-base font-bold text-deep">{section.title}</h2>
                {section.items.length === 0 ? (
                  <p className="text-xs text-muted">No amendments required for this stage.</p>
                ) : (
                  <div className="space-y-3">
                    {section.items.map((item, idx) => (
                      <div key={idx} className="rounded-xl bg-cream border border-[#176B35]/10 p-4 space-y-1.5">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm font-bold text-ink">{item.amendment_name}</p>
                          <span className="rounded-lg bg-mint px-2.5 py-0.5 text-xs font-bold text-forest shrink-0">
                            {item.quantity_kg_total} kg total
                          </span>
                        </div>
                        <p className="text-xs text-muted">
                          Rate: {item.quantity_per_acre_kg} kg/acre • {item.application_timing}
                        </p>
                        <p className="text-xs text-ink/90">
                          <strong>Why:</strong> {item.reason}
                        </p>
                        <p className="text-[11px] text-muted">
                          Price:{" "}
                          {item.price_inr !== null && item.price_inr !== undefined
                            ? `₹${item.price_inr} (${item.price_source}, verified ${item.price_verified_date})`
                            : "Unavailable (no verified dated MRP source configured)"}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

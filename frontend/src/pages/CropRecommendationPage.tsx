import React, { useEffect, useState } from "react";
import { Sprout } from "lucide-react";
import { CardSkeleton, EmptyState, ErrorState } from "@/components/common/StateFeedback";
import { useAsyncState } from "@/hooks/useAsyncState";
import { api } from "@/services/api";
import type { CropRecommendationResponse } from "@/types";

export const CropRecommendationPage: React.FC = () => {
  const [season, setSeason] = useState("Kharif");
  const [water, setWater] = useState("moderate");
  const [budget, setBudget] = useState("moderate");
  const [includeHorticulture, setIncludeHorticulture] = useState(true);
  const [temp, setTemp] = useState("");
  const [rainfall, setRainfall] = useState("");

  const { data, loading, error, run } = useAsyncState<CropRecommendationResponse>();

  const fetchRecommendations = () => {
    void run(() =>
      api.recommendCrops({
        season,
        water_availability: water,
        budget_level: budget,
        include_horticulture: includeHorticulture,
        avg_temp_c: temp ? Number(temp) : null,
        annual_rainfall_mm: rainfall ? Number(rainfall) : null,
      })
    );
  };

  useEffect(() => {
    fetchRecommendations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-deep">Crop Recommendation</h1>
        <p className="text-sm text-muted mt-1">
          Matches cereals, pulses, oilseeds, vegetables, and fruits to your soil status, season, water availability, and budget.
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          fetchRecommendations();
        }}
        className="rm-card p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 items-end"
      >
        <div>
          <label className="block text-xs font-semibold mb-1">Season</label>
          <select className="rm-input" value={season} onChange={(e) => setSeason(e.target.value)}>
            <option value="Kharif">Kharif</option>
            <option value="Rabi">Rabi</option>
            <option value="Zaid">Zaid (Summer)</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Water Availability</label>
          <select className="rm-input" value={water} onChange={(e) => setWater(e.target.value)}>
            <option value="low">Low / Rainfed</option>
            <option value="moderate">Moderate / Borewell</option>
            <option value="high">High / Canal</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Budget Tier</label>
          <select className="rm-input" value={budget} onChange={(e) => setBudget(e.target.value)}>
            <option value="low">Low</option>
            <option value="moderate">Moderate</option>
            <option value="high">High</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Temp °C (Optional)</label>
          <input type="number" className="rm-input" value={temp} onChange={(e) => setTemp(e.target.value)} placeholder="e.g. 28" />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Rainfall mm (Opt)</label>
          <input type="number" className="rm-input" value={rainfall} onChange={(e) => setRainfall(e.target.value)} placeholder="e.g. 750" />
        </div>
        <button type="submit" className="rm-btn-primary">
          <Sprout className="h-4 w-4" />
          Recommend
        </button>

        <label className="sm:col-span-2 lg:col-span-6 flex items-center gap-2 text-xs text-ink cursor-pointer pt-1">
          <input
            type="checkbox"
            checked={includeHorticulture}
            onChange={(e) => setIncludeHorticulture(e.target.checked)}
            className="rounded border-forest text-forest"
          />
          Include vegetables and fruit crops
        </label>
      </form>

      {loading && !data ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <CardSkeleton lines={4} />
          <CardSkeleton lines={4} />
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={fetchRecommendations} />
      ) : !data || data.recommendations.length === 0 ? (
        <EmptyState title="No recommendations found" description="Adjust season or water availability filters." />
      ) : (
        <div className="space-y-4">
          <div className="rm-surface p-4 text-xs flex flex-wrap items-center justify-between gap-2">
            <span>
              <strong>Basis:</strong> {data.location_summary} • {data.soil_source_used}
            </span>
            {data.missing_soil_fields.length > 0 && (
              <span className="text-[#8A5B00]">
                Missing soil fields: {data.missing_soil_fields.join(", ")}
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.recommendations.map((item) => (
              <div key={item.crop_name} className="rm-card p-5 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span className="rounded-full bg-mint px-2.5 py-0.5 text-[11px] font-semibold uppercase text-forest">
                      {item.category}
                    </span>
                    <h3 className="text-lg font-bold text-deep mt-1">{item.crop_name}</h3>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-muted">Suitability</span>
                    <p className="text-lg font-extrabold text-forest">{item.suitability_score}%</p>
                  </div>
                </div>

                <ul className="space-y-1 text-xs text-ink/90 list-disc pl-4">
                  {item.reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>

                <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-[#176B35]/10">
                  <div>
                    <span className="text-muted">Duration:</span>
                    <p className="font-semibold">{item.duration_days}</p>
                  </div>
                  <div>
                    <span className="text-muted">Expected Yield:</span>
                    <p className="font-semibold">{item.expected_yield_per_acre}</p>
                  </div>
                  <div>
                    <span className="text-muted">Est. Cost / Acre:</span>
                    <p className="font-semibold">{item.estimated_cost_per_acre_inr}</p>
                  </div>
                  <div>
                    <span className="text-muted">Water Need:</span>
                    <p className="font-semibold">{item.water_requirement}</p>
                  </div>
                </div>
                <p className="text-xs text-muted">
                  <strong>Nutrients:</strong> {item.nutrient_needs}
                </p>
                <p className="text-[11px] text-forest font-medium">{item.market_value_note}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

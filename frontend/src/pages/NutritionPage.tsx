import React, { useEffect, useState } from "react";
import { Apple, Search, BookOpen, ShieldAlert, ExternalLink } from "lucide-react";
import {
  CardSkeleton,
  EmptyState,
  ErrorState,
  IntegrationStatusBadge,
} from "@/components/common/StateFeedback";
import { useAsyncState } from "@/hooks/useAsyncState";
import { api } from "@/services/api";
import type { NutritionResponse } from "@/types";

export const NutritionPage: React.FC = () => {
  const [query, setQuery] = useState("ragi");
  const { data, loading, error, run } = useAsyncState<NutritionResponse>();

  const handleSearch = (e?: React.FormEvent) => {
    e?.preventDefault();
    void run(() => api.getNutrition(query));
  };

  useEffect(() => {
    void run(() => api.getNutrition("ragi"));
  }, [run]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-deep">Nutrition & Crop Utilization</h1>
          <p className="text-sm text-muted mt-1">
            Composition, preparation, storage, and value addition from ICMR-NIN IFCT, FAO/INFOODS, USDA FDC, and PubMed.
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            className="rm-input w-56"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search crop (e.g. ragi, tomato)"
          />
          <button type="submit" className="rm-btn-primary">
            <Search className="h-4 w-4" />
            Search
          </button>
        </form>
      </div>

      {loading && !data ? (
        <CardSkeleton lines={5} />
      ) : error ? (
        <ErrorState message={error} onRetry={() => handleSearch()} />
      ) : !data ? (
        <EmptyState title="Search any crop or food" description="Inspect verified nutritional composition and value-addition guides." />
      ) : (
        <div className="space-y-6">
          <div className="rounded-2xl border border-warning/40 bg-warning/10 p-4 flex items-start gap-2.5 text-xs text-[#6B4600]">
            <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{data.medical_disclaimer}</span>
          </div>

          {/* Established Evidence */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rm-card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-deep flex items-center gap-2">
                  <Apple className="h-4 w-4 text-forest" />
                  Established Composition (ICMR-NIN / USDA / FAO)
                </h2>
                <span className="rounded-full bg-mint px-2.5 py-0.5 text-[11px] font-semibold text-forest">
                  Established Evidence
                </span>
              </div>

              {data.established_sources.icmr_nin_ifct ? (
                <div className="rounded-xl bg-mint/60 p-4 space-y-2 text-xs">
                  <p className="font-bold text-deep">
                    {String(data.established_sources.icmr_nin_ifct.food_name)}
                  </p>
                  <p className="text-muted">
                    Source: {String(data.established_sources.icmr_nin_ifct.source)}
                  </p>
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    {Object.entries(
                      (data.established_sources.icmr_nin_ifct.per_100g as Record<string, unknown>) || {}
                    ).map(([k, v]) => (
                      <div key={k} className="rounded-lg bg-white px-2.5 py-1.5 flex justify-between">
                        <span className="text-muted">{k}</span>
                        <span className="font-bold text-ink">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-xs text-muted">
                  No local ICMR-NIN IFCT summary cached for "{data.crop_or_food}". Try Ragi, Tomato, Paddy, Banana, or Groundnut, or configure USDA FDC key below.
                </p>
              )}

              <div className="pt-2 border-t border-[#176B35]/10 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-ink">USDA FoodData Central API</span>
                  <IntegrationStatusBadge status={data.established_sources.usda_fdc_status} />
                </div>
                {data.established_sources.usda_fdc_results.length > 0 && (
                  <div className="space-y-2">
                    {data.established_sources.usda_fdc_results.map((item, idx) => (
                      <div key={idx} className="rounded-xl bg-cream p-3 text-xs">
                        <p className="font-semibold text-deep">{String(item.description)}</p>
                        <p className="text-[11px] text-muted">FDC ID: {String(item.fdc_id)}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="text-[11px] text-muted pt-1">
                <strong>FAO/INFOODS Tagnames:</strong>{" "}
                {data.established_sources.fao_infoods_tagnames.slice(0, 5).join(", ")}
              </div>
            </div>

            {/* Utilization */}
            <div className="rm-card p-5 space-y-4">
              <h2 className="text-base font-bold text-deep">Preparation, Storage & Value Addition</h2>
              <div className="space-y-3 text-xs">
                <div className="rm-surface p-3.5">
                  <p className="font-bold text-deep mb-1">Preparation</p>
                  <ul className="list-disc pl-4 space-y-1">
                    {data.utilization.preparation.map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </div>
                <div className="rm-surface p-3.5">
                  <p className="font-bold text-deep mb-1">Post-Harvest Storage</p>
                  <ul className="list-disc pl-4 space-y-1">
                    {data.utilization.storage.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-xl bg-cream border border-[#176B35]/10 p-3.5">
                  <p className="font-bold text-deep mb-1">Processing & Value Addition</p>
                  <ul className="list-disc pl-4 space-y-1">
                    {data.utilization.processing_and_value_addition.map((v, i) => (
                      <li key={i}>{v}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Preliminary Research (PubMed) */}
          <div className="rm-card p-5 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-base font-bold text-deep flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-forest" />
                Preliminary Research Literature (PubMed E-utilities)
              </h2>
              <span className="rounded-full bg-warning/20 text-[#8A5B00] px-2.5 py-0.5 text-[11px] font-semibold">
                Preliminary Research — Not Medical Advice
              </span>
            </div>
            <p className="text-xs text-muted">{data.preliminary_research.disclaimer}</p>
            {data.preliminary_research.articles.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {data.preliminary_research.articles.map((art) => (
                  <a
                    key={art.pmid}
                    href={art.url}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-xl bg-cream border border-[#176B35]/10 p-3.5 hover:border-forest/40 transition-colors block"
                  >
                    <p className="text-xs font-bold text-deep flex items-start justify-between gap-2">
                      <span>{art.title}</span>
                      <ExternalLink className="h-3.5 w-3.5 shrink-0 text-forest" />
                    </p>
                    <p className="text-[11px] text-muted mt-1">
                      {art.journal} • {art.pub_date} • PMID {art.pmid}
                    </p>
                  </a>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted">
                No PubMed summaries retrieved (offline sandbox or no matching records).
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

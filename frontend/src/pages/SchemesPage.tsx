import React, { useEffect, useState } from "react";
import { Landmark, ExternalLink, Search } from "lucide-react";
import {
  CardSkeleton,
  EmptyState,
  ErrorState,
  IntegrationStatusBadge,
} from "@/components/common/StateFeedback";
import { useAuth } from "@/context/AuthContext";
import { useAsyncState } from "@/hooks/useAsyncState";
import { api } from "@/services/api";
import type { SchemesResponse } from "@/types";

export const SchemesPage: React.FC = () => {
  const { farmer } = useAuth();
  const [stateFilter, setStateFilter] = useState(farmer?.state || "Karnataka");
  const [districtFilter, setDistrictFilter] = useState(farmer?.district || "");
  const [categoryFilter, setCategoryFilter] = useState(farmer?.farmer_category || "");
  const [cropFilter, setCropFilter] = useState(farmer?.main_crops?.[0] || "");

  const { data, loading, error, run } = useAsyncState<SchemesResponse>();

  const loadSchemes = () => {
    void run(() =>
      api.getSchemes({
        state: stateFilter.trim() || undefined,
        district: districtFilter.trim() || undefined,
        category: categoryFilter.trim() || undefined,
        crop: cropFilter.trim() || undefined,
      })
    );
  };

  useEffect(() => {
    loadSchemes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-deep">Government Schemes</h1>
        <p className="text-sm text-muted mt-1">
          Official central and state schemes with verified `.gov.in` portals, document checklists, and last-verified dates.
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          loadSchemes();
        }}
        className="rm-card p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end"
      >
        <div>
          <label className="block text-xs font-semibold mb-1">State</label>
          <input className="rm-input" value={stateFilter} onChange={(e) => setStateFilter(e.target.value)} />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">District</label>
          <input className="rm-input" value={districtFilter} onChange={(e) => setDistrictFilter(e.target.value)} placeholder="Optional" />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Farmer Category</label>
          <select className="rm-input" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            <option value="">All Categories</option>
            <option value="marginal">Marginal</option>
            <option value="small">Small</option>
            <option value="medium">Medium</option>
            <option value="large">Large</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Crop</label>
          <input className="rm-input" value={cropFilter} onChange={(e) => setCropFilter(e.target.value)} placeholder="e.g. Paddy, Tomato" />
        </div>
        <button type="submit" className="rm-btn-primary">
          <Search className="h-4 w-4" />
          Filter Schemes
        </button>
      </form>

      {data && (
        <div className="flex flex-wrap gap-3 text-xs">
          <div className="rm-card px-4 py-2 flex items-center gap-2">
            <span className="font-semibold">API Setu myScheme:</span>
            <IntegrationStatusBadge status={data.apisetu_status} />
          </div>
          <div className="rm-card px-4 py-2 flex items-center gap-2">
            <span className="font-semibold">data.gov.in Schemes:</span>
            <IntegrationStatusBadge status={data.data_gov_status} />
          </div>
        </div>
      )}

      {loading && !data ? (
        <CardSkeleton lines={5} />
      ) : error ? (
        <ErrorState message={error} onRetry={loadSchemes} />
      ) : !data || data.schemes.length === 0 ? (
        <EmptyState title="No schemes match your filters" description="Broaden state or crop filters to view central schemes." />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {data.schemes.map((s) => (
            <div key={s.id} className="rm-card p-6 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="rounded-full bg-mint px-2.5 py-0.5 text-[11px] font-bold text-forest">
                    {s.level} • {s.state}
                  </span>
                  <h2 className="text-lg font-bold text-deep mt-1.5 flex items-center gap-2">
                    <Landmark className="h-4 w-4 text-forest shrink-0" />
                    {s.name}
                  </h2>
                </div>
                <span className="text-[11px] text-muted shrink-0">Verified {s.last_verified}</span>
              </div>

              <p className="text-xs text-ink font-medium leading-relaxed">{s.benefits}</p>

              <div className="text-xs space-y-2">
                <div>
                  <p className="font-bold text-deep">Official Eligibility</p>
                  <ul className="list-disc pl-4 text-muted space-y-0.5">
                    {s.eligibility.map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="font-bold text-deep">Documents Required</p>
                  <p className="text-muted">{s.documents_required.join(" • ")}</p>
                </div>
                <div>
                  <p className="font-bold text-deep">Application Steps</p>
                  <ol className="list-decimal pl-4 text-muted space-y-0.5">
                    {s.application_steps.map((st, i) => (
                      <li key={i}>{st}</li>
                    ))}
                  </ol>
                </div>
              </div>

              <div className="pt-2 border-t border-[#176B35]/10 flex items-center justify-between text-xs">
                <span className="text-muted truncate pr-2">{s.source}</span>
                <a
                  href={s.official_url}
                  target="_blank"
                  rel="noreferrer"
                  className="rm-btn-secondary py-1.5 px-3 text-xs shrink-0"
                >
                  Apply on Official Portal
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

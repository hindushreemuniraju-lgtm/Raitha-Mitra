import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { Store, Search, AlertTriangle } from "lucide-react";
import {
  CardSkeleton,
  EmptyState,
  ErrorState,
  IntegrationStatusBadge,
} from "@/components/common/StateFeedback";
import { useAuth } from "@/context/AuthContext";
import { useAsyncState } from "@/hooks/useAsyncState";
import { api } from "@/services/api";
import type { MandiResponse } from "@/types";

export const MandiPage: React.FC = () => {
  const { farmer } = useAuth();
  const [commodity, setCommodity] = useState(farmer?.main_crops?.[0] || "");
  const [stateFilter, setStateFilter] = useState(farmer?.state || "");
  const [districtFilter, setDistrictFilter] = useState(farmer?.district || "");
  const [marketFilter, setMarketFilter] = useState("");
  const [dateFilter, setDateFilter] = useState("");
  const [includeDemo, setIncludeDemo] = useState(false);

  const { data, loading, error, run } = useAsyncState<MandiResponse>();

  const loadPrices = (demoFlag = includeDemo) => {
    void run(() =>
      api.getMandiPrices({
        commodity: commodity.trim() || undefined,
        state: stateFilter.trim() || undefined,
        district: districtFilter.trim() || undefined,
        market: marketFilter.trim() || undefined,
        date: dateFilter.trim() || undefined,
        include_demo: demoFlag,
      })
    );
  };

  useEffect(() => {
    loadPrices(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-deep">Mandi Prices</h1>
          <p className="text-sm text-muted mt-1">
            Sourced from AGMARKNET (data.gov.in), CEDA Agmarknet, and e-NAM. Always labelled as latest available daily data.
          </p>
        </div>
        {data && (
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-bold ${
              data.is_demo_data
                ? "bg-warning/20 text-[#6B4600] border border-warning/50"
                : "bg-mint text-forest border border-leaf/30"
            }`}
          >
            {data.label}
          </span>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          loadPrices(includeDemo);
        }}
        className="rm-card p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 items-end"
      >
        <div>
          <label className="block text-xs font-semibold mb-1">Crop / Commodity</label>
          <input className="rm-input" value={commodity} onChange={(e) => setCommodity(e.target.value)} placeholder="e.g. Tomato" />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">State</label>
          <input className="rm-input" value={stateFilter} onChange={(e) => setStateFilter(e.target.value)} placeholder="Karnataka" />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">District</label>
          <input className="rm-input" value={districtFilter} onChange={(e) => setDistrictFilter(e.target.value)} placeholder="Mandya" />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Market</label>
          <input className="rm-input" value={marketFilter} onChange={(e) => setMarketFilter(e.target.value)} placeholder="Optional" />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Date</label>
          <input type="date" className="rm-input" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} />
        </div>
        <button type="submit" className="rm-btn-primary">
          <Search className="h-4 w-4" />
          Search
        </button>
      </form>

      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {Object.entries(data.source_statuses).map(([key, info]) => (
            <div key={key} className="rm-card p-3.5 flex items-center justify-between gap-2 text-xs">
              <div>
                <p className="font-bold text-deep uppercase">{key.replace("_", " ")}</p>
                <p className="text-muted text-[11px] mt-0.5">{info.note}</p>
              </div>
              <IntegrationStatusBadge status={info.status} />
            </div>
          ))}
        </div>
      )}

      {loading && !data ? (
        <CardSkeleton lines={5} />
      ) : error ? (
        <ErrorState message={error} onRetry={() => loadPrices(includeDemo)} />
      ) : !data || data.records.length === 0 ? (
        <EmptyState
          title="No live mandi records returned"
          description="Live AGMARKNET / CEDA API keys are not configured in backend/.env. You can inspect the UI layout using clearly labelled DEMO DATA."
          action={
            <button
              type="button"
              onClick={() => {
                setIncludeDemo(true);
                loadPrices(true);
              }}
              className="rm-btn-secondary"
            >
              Load Labelled DEMO DATA Sample
            </button>
          }
        />
      ) : (
        <div className="space-y-6">
          {data.is_demo_data && (
            <div className="rounded-2xl border border-warning/50 bg-warning/15 p-4 flex items-center gap-2.5 text-xs font-semibold text-[#6B4600]">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>
                DEMO DATA ACTIVE: The rows and charts below are sample placeholders for UI preview only—not real mandi prices.
              </span>
            </div>
          )}

          {/* Market Comparison Chart */}
          <div className="rm-card p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-deep flex items-center gap-2">
                <Store className="h-4 w-4 text-forest" />
                Cross-Market Modal Price Comparison (₹ / quintal)
              </h2>
              {data.updated_at && (
                <span className="text-[11px] text-muted">Updated: {data.updated_at}</span>
              )}
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.market_comparison}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#DCE8D5" />
                  <XAxis dataKey="market" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="modal_price_inr" name="Modal Price (₹/qtl)" fill="#176B35" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Table */}
          <div className="rm-card p-5 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-muted border-b border-[#176B35]/15">
                  <th className="py-2.5 pr-3">Commodity</th>
                  <th className="py-2.5 pr-3">Market</th>
                  <th className="py-2.5 pr-3">District / State</th>
                  <th className="py-2.5 pr-3">Min ₹</th>
                  <th className="py-2.5 pr-3">Max ₹</th>
                  <th className="py-2.5 pr-3">Modal ₹</th>
                  <th className="py-2.5 pr-3">Arrivals (t)</th>
                  <th className="py-2.5">Date & Source</th>
                </tr>
              </thead>
              <tbody>
                {data.records.map((r, idx) => (
                  <tr key={idx} className="border-b border-[#176B35]/5">
                    <td className="py-2.5 pr-3 font-bold text-deep">
                      {r.commodity} <span className="font-normal text-muted">({r.variety})</span>
                    </td>
                    <td className="py-2.5 pr-3">{r.market}</td>
                    <td className="py-2.5 pr-3 text-muted">
                      {r.district}, {r.state}
                    </td>
                    <td className="py-2.5 pr-3">₹{r.min_price_inr}</td>
                    <td className="py-2.5 pr-3">₹{r.max_price_inr}</td>
                    <td className="py-2.5 pr-3 font-bold text-forest">₹{r.modal_price_inr}</td>
                    <td className="py-2.5 pr-3">{r.arrivals_tonnes ?? "—"}</td>
                    <td className="py-2.5 text-muted">
                      {r.price_date} • {r.source}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

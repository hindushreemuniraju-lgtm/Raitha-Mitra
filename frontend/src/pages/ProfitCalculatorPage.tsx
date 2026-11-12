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
import { Calculator, Info } from "lucide-react";
import { ErrorState, SuccessBanner } from "@/components/common/StateFeedback";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/services/api";
import type { ProfitScenarioResult } from "@/types";

export const ProfitCalculatorPage: React.FC = () => {
  const { farmer } = useAuth();
  const [cropName, setCropName] = useState(farmer?.main_crops?.[0] || "Tomato");
  const [acres, setAcres] = useState(String(farmer?.farm_size_acres || 2));
  const [seedCost, setSeedCost] = useState("4500");
  const [fertilizerCost, setFertilizerCost] = useState("9000");
  const [pesticideCost, setPesticideCost] = useState("6000");
  const [labourCost, setLabourCost] = useState("18000");
  const [irrigationCost, setIrrigationCost] = useState("4000");
  const [transportCost, setTransportCost] = useState("5000");
  const [otherCost, setOtherCost] = useState("2500");
  const [yieldPerAcre, setYieldPerAcre] = useState("100");
  const [pricePerQtl, setPricePerQtl] = useState("1400");

  const [result, setResult] = useState<ProfitScenarioResult | null>(null);
  const [history, setHistory] = useState<ProfitScenarioResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedNotice, setSavedNotice] = useState<string | null>(null);

  useEffect(() => {
    api
      .getProfitScenarios()
      .then(setHistory)
      .catch(() => {});
  }, []);

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSavedNotice(null);
    try {
      const res = await api.calculateProfit({
        crop_name: cropName,
        farm_size_acres: Number(acres) || 1,
        seed_cost: Number(seedCost) || 0,
        fertilizer_cost: Number(fertilizerCost) || 0,
        pesticide_cost: Number(pesticideCost) || 0,
        labour_cost: Number(labourCost) || 0,
        irrigation_cost: Number(irrigationCost) || 0,
        transport_cost: Number(transportCost) || 0,
        other_cost: Number(otherCost) || 0,
        expected_yield_qtl_per_acre: Number(yieldPerAcre) || 1,
        expected_price_per_qtl: Number(pricePerQtl) || 1,
        save_scenario: true,
      });
      setResult(res);
      setHistory((prev) => [res, ...prev]);
      setSavedNotice("Editable scenario calculated and saved to your farm history.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to compute profit");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-deep">Farm Profit Calculator</h1>
        <p className="text-sm text-muted mt-1">
          Adjust every cost, yield, and price assumption to compare Low, Expected, and Optimistic outcomes.
        </p>
      </div>

      <div className="rounded-2xl border border-[#176B35]/15 bg-mint/60 p-3.5 text-xs text-deep flex items-center gap-2">
        <Info className="h-4 w-4 text-forest shrink-0" />
        <span>All assumptions remain editable. Estimates are planning projections and are never guaranteed.</span>
      </div>

      {savedNotice && <SuccessBanner message={savedNotice} />}
      {error && <ErrorState message={error} />}

      <form onSubmit={handleCalculate} className="rm-card p-6 space-y-4">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="col-span-2 sm:col-span-1">
            <label className="block text-xs font-semibold mb-1">Crop</label>
            <input className="rm-input" required value={cropName} onChange={(e) => setCropName(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Acres</label>
            <input type="number" step="0.1" className="rm-input" value={acres} onChange={(e) => setAcres(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Seed (₹)</label>
            <input type="number" className="rm-input" value={seedCost} onChange={(e) => setSeedCost(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Fertilizer (₹)</label>
            <input type="number" className="rm-input" value={fertilizerCost} onChange={(e) => setFertilizerCost(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Pesticide (₹)</label>
            <input type="number" className="rm-input" value={pesticideCost} onChange={(e) => setPesticideCost(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Labour (₹)</label>
            <input type="number" className="rm-input" value={labourCost} onChange={(e) => setLabourCost(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Irrigation (₹)</label>
            <input type="number" className="rm-input" value={irrigationCost} onChange={(e) => setIrrigationCost(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Transport (₹)</label>
            <input type="number" className="rm-input" value={transportCost} onChange={(e) => setTransportCost(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Other Costs (₹)</label>
            <input type="number" className="rm-input" value={otherCost} onChange={(e) => setOtherCost(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Yield (qtl/acre)</label>
            <input type="number" step="0.5" className="rm-input" value={yieldPerAcre} onChange={(e) => setYieldPerAcre(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Price (₹/qtl)</label>
            <input type="number" className="rm-input" value={pricePerQtl} onChange={(e) => setPricePerQtl(e.target.value)} />
          </div>
          <div className="flex items-end">
            <button type="submit" disabled={loading} className="rm-btn-primary w-full">
              <Calculator className="h-4 w-4" />
              {loading ? "..." : "Calculate"}
            </button>
          </div>
        </div>
      </form>

      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="rm-card p-4">
              <span className="text-xs text-muted">Total Cost</span>
              <p className="text-xl font-bold text-ink mt-1">₹{result.total_cost.toLocaleString("en-IN")}</p>
            </div>
            <div className="rm-card p-4">
              <span className="text-xs text-muted">Expected Revenue</span>
              <p className="text-xl font-bold text-deep mt-1">₹{result.expected_revenue.toLocaleString("en-IN")}</p>
            </div>
            <div className="rm-card p-4">
              <span className="text-xs text-muted">Net Profit</span>
              <p className={`text-xl font-extrabold mt-1 ${result.net_profit >= 0 ? "text-forest" : "text-danger"}`}>
                ₹{result.net_profit.toLocaleString("en-IN")}
              </p>
            </div>
            <div className="rm-card p-4">
              <span className="text-xs text-muted">Profit / Acre</span>
              <p className="text-xl font-bold text-deep mt-1">₹{result.profit_per_acre.toLocaleString("en-IN")}</p>
            </div>
            <div className="rm-card p-4">
              <span className="text-xs text-muted">Margin & Breakeven</span>
              <p className="text-lg font-bold text-deep mt-1">{result.margin_pct}%</p>
              <p className="text-[11px] text-muted">Breakeven ₹{result.breakeven_price_per_qtl}/qtl</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rm-card p-5 space-y-3">
              <h2 className="text-base font-bold text-deep">Low / Expected / Optimistic Scenarios</h2>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={result.scenarios}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#DCE8D5" />
                    <XAxis dataKey="scenario" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="revenue" name="Revenue (₹)" fill="#56A832" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="net_profit" name="Net Profit (₹)" fill="#176B35" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rm-card p-5 space-y-3">
              <h2 className="text-base font-bold text-deep">Scenario Comparison Table</h2>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-muted border-b border-[#176B35]/10">
                    <th className="py-2">Scenario</th>
                    <th className="py-2">Qty (qtl)</th>
                    <th className="py-2">Price ₹</th>
                    <th className="py-2">Net Profit ₹</th>
                    <th className="py-2">Margin</th>
                  </tr>
                </thead>
                <tbody>
                  {result.scenarios.map((s) => (
                    <tr key={s.scenario} className="border-b border-[#176B35]/5">
                      <td className="py-2.5 font-bold text-deep">{s.scenario}</td>
                      <td className="py-2.5">{s.yield_qtl_total}</td>
                      <td className="py-2.5">₹{s.price_per_qtl}</td>
                      <td className="py-2.5 font-bold text-forest">₹{s.net_profit.toLocaleString("en-IN")}</td>
                      <td className="py-2.5">{s.margin_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-[11px] text-muted pt-1">{result.disclaimer}</p>
            </div>
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div className="rm-card p-5 space-y-2">
          <h2 className="text-sm font-bold text-deep">Saved Profit Calculations</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            {history.slice(0, 6).map((h, i) => (
              <button
                key={h.id ?? i}
                type="button"
                onClick={() => setResult(h)}
                className="rounded-xl bg-cream border border-[#176B35]/10 p-3 text-left hover:border-forest/40"
              >
                <p className="font-bold text-deep">
                  {h.crop_name} ({h.farm_size_acres} ac)
                </p>
                <p className="text-forest font-semibold mt-0.5">
                  Net ₹{h.net_profit.toLocaleString("en-IN")} ({h.margin_pct}%)
                </p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

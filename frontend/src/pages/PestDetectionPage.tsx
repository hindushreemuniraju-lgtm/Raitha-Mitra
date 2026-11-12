import React, { useEffect, useState } from "react";
import { Bug, Camera, AlertTriangle } from "lucide-react";
import {
  CardSkeleton,
  EmptyState,
  ErrorState,
  IntegrationStatusBadge,
} from "@/components/common/StateFeedback";
import { api } from "@/services/api";
import type { DiseaseScan } from "@/types";

export const PestDetectionPage: React.FC = () => {
  const [scans, setScans] = useState<DiseaseScan[]>([]);
  const [cropName, setCropName] = useState("");
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latestScan, setLatestScan] = useState<DiseaseScan | null>(null);

  const loadScans = () => {
    setLoading(true);
    api
      .getDiseaseScans()
      .then((res) => {
        setScans(res);
        if (res.length > 0 && !latestScan) {
          setLatestScan(res[0]);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load scan history"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadScans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAnalyzing(true);
    setError(null);
    try {
      const scan = await api.analyzeDiseaseImage(file, cropName.trim() || undefined);
      setLatestScan(scan);
      setScans((prev) => [scan, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze crop image");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-deep">Pest & Disease Detection</h1>
        <p className="text-sm text-muted mt-1">
          Capture or upload a clear close-up photo of affected leaves or stems. Uses verified Plantix B2B adapter or configured vision fallback—never fabricates AI results.
        </p>
      </div>

      {error && <ErrorState message={error} />}

      <div className="rm-card p-6 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold mb-1">Crop Name (Optional)</label>
            <input
              className="rm-input"
              value={cropName}
              onChange={(e) => setCropName(e.target.value)}
              placeholder="e.g. Tomato, Paddy, Chilli"
            />
          </div>
          <label className="rm-btn-primary cursor-pointer justify-center">
            <Camera className="h-4 w-4" />
            <span>{analyzing ? "Analyzing Photo..." : "Capture or Upload Leaf Image"}</span>
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handlePhotoUpload}
              className="sr-only"
              disabled={analyzing}
            />
          </label>
        </div>
      </div>

      {latestScan && (
        <div className="rm-card p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-deep flex items-center gap-2">
                <Bug className="h-5 w-5 text-forest" />
                {latestScan.diagnosis_name || "Analysis Result"}
              </h2>
              <p className="text-xs text-muted mt-0.5">
                Adapter: {latestScan.adapter_used} • Crop: {latestScan.crop_name || "Auto"}
                {latestScan.confidence !== null && latestScan.confidence !== undefined
                  ? ` • Confidence: ${(latestScan.confidence * 100).toFixed(0)}%`
                  : ""}
              </p>
            </div>
            <IntegrationStatusBadge
              status={latestScan.status === "diagnosed" ? "configured" : "not_configured"}
              label={latestScan.status.replace("_", " ")}
            />
          </div>

          {latestScan.status === "not_configured" && (
            <div className="rounded-xl border border-warning/40 bg-warning/10 p-4 text-xs text-[#6B4600] flex items-start gap-2.5">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Disease recognition API is not configured.</p>
                <p className="mt-0.5">
                  {latestScan.raw_summary ||
                    "Configure Plantix B2B credentials (PLANTIX_BASE_URL, PLANTIX_API_KEY) or a fallback vision model in backend/.env."}
                </p>
              </div>
            </div>
          )}

          {latestScan.status === "uncertain" && (
            <div className="rounded-xl border border-warning/40 bg-warning/10 p-4 text-xs text-[#6B4600]">
              <strong>Uncertain diagnosis:</strong> Confidence is low. Please take a sharper photo in bright indirect daylight showing both sides of an affected leaf and upload again.
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="rm-surface p-4 space-y-1.5">
              <p className="font-bold text-deep">Observed Symptoms</p>
              {latestScan.symptoms.length > 0 ? (
                <ul className="list-disc pl-4 space-y-1">
                  {latestScan.symptoms.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted">No symptoms returned.</p>
              )}
            </div>

            <div className="rm-surface p-4 space-y-1.5">
              <p className="font-bold text-deep">Organic Treatment</p>
              {latestScan.organic_treatments.length > 0 ? (
                <ul className="list-disc pl-4 space-y-1">
                  {latestScan.organic_treatments.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted">None listed.</p>
              )}
            </div>

            <div className="rounded-2xl bg-cream border border-[#176B35]/10 p-4 space-y-1.5">
              <p className="font-bold text-deep">Chemical Treatment (Follow Label Dose)</p>
              {latestScan.chemical_treatments.length > 0 ? (
                <ul className="list-disc pl-4 space-y-1">
                  {latestScan.chemical_treatments.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted">None listed.</p>
              )}
            </div>

            <div className="rounded-2xl bg-cream border border-[#176B35]/10 p-4 space-y-1.5">
              <p className="font-bold text-deep">Prevention & Precautions</p>
              {latestScan.precautions.length > 0 ? (
                <ul className="list-disc pl-4 space-y-1">
                  {latestScan.precautions.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted">None listed.</p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="space-y-3">
        <h2 className="text-lg font-bold text-deep">Recent Scan History</h2>
        {loading ? (
          <CardSkeleton lines={3} />
        ) : scans.length === 0 ? (
          <EmptyState
            title="No scans uploaded yet"
            description="Upload a leaf photo above to inspect crop health."
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {scans.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => setLatestScan(s)}
                className="rm-card p-4 text-left hover:border-forest/40 transition-colors"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-bold text-ink truncate">
                    {s.diagnosis_name || s.status.replace("_", " ")}
                  </span>
                  <IntegrationStatusBadge
                    status={s.status === "diagnosed" ? "configured" : "not_configured"}
                    label={s.status}
                  />
                </div>
                <p className="text-xs text-muted mt-1">
                  {s.crop_name || "Unknown crop"} • {s.adapter_used}
                </p>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

import React, { useEffect, useState } from "react";
import { Upload, CheckCircle2, MapPin, TestTube2 } from "lucide-react";
import { MediaPreview } from "@/components/common/MediaPreview";
import {
  CardSkeleton,
  EmptyState,
  ErrorState,
  SuccessBanner,
} from "@/components/common/StateFeedback";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/services/api";
import type { SoilRecord, SoilUploadExtraction } from "@/types";

export const SoilHealthPage: React.FC = () => {
  const { farmer } = useAuth();
  const [records, setRecords] = useState<SoilRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Upload state
  const [sourceType, setSourceType] = useState<"soil_health_card" | "lab_report">("soil_health_card");
  const [uploading, setUploading] = useState(false);
  const [pendingExtraction, setPendingExtraction] = useState<SoilUploadExtraction | null>(null);
  const [instantPreview, setInstantPreview] = useState<{
    url: string;
    filename: string;
    mimeType: string;
    kind: "image" | "pdf";
  } | null>(null);

  // Review form state
  const [ph, setPh] = useState("");
  const [nitrogen, setNitrogen] = useState("");
  const [phosphorus, setPhosphorus] = useState("");
  const [potassium, setPotassium] = useState("");
  const [oc, setOc] = useState("");
  const [ec, setEc] = useState("");
  const [zinc, setZinc] = useState("");
  const [boron, setBoron] = useState("");
  const [reviewNotes, setReviewNotes] = useState("");
  const [confirming, setConfirming] = useState(false);

  // Dataset estimate state
  const [estLat, setEstLat] = useState(
    farmer?.gps_consent && farmer.latitude ? String(farmer.latitude) : ""
  );
  const [estLon, setEstLon] = useState(
    farmer?.gps_consent && farmer.longitude ? String(farmer.longitude) : ""
  );
  const [estimating, setEstimating] = useState(false);

  const loadRecords = () => {
    setLoading(true);
    api
      .getSoilRecords()
      .then((res) => setRecords(res))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load soil records"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadRecords();
  }, []);

  const populateReviewForm = (rec: SoilRecord) => {
    setPh(rec.ph !== null && rec.ph !== undefined ? String(rec.ph) : "");
    setNitrogen(rec.nitrogen_kg_ha !== null && rec.nitrogen_kg_ha !== undefined ? String(rec.nitrogen_kg_ha) : "");
    setPhosphorus(rec.phosphorus_kg_ha !== null && rec.phosphorus_kg_ha !== undefined ? String(rec.phosphorus_kg_ha) : "");
    setPotassium(rec.potassium_kg_ha !== null && rec.potassium_kg_ha !== undefined ? String(rec.potassium_kg_ha) : "");
    setOc(rec.organic_carbon_pct !== null && rec.organic_carbon_pct !== undefined ? String(rec.organic_carbon_pct) : "");
    setEc(rec.ec_ds_m !== null && rec.ec_ds_m !== undefined ? String(rec.ec_ds_m) : "");
    setZinc(rec.zinc_ppm !== null && rec.zinc_ppm !== undefined ? String(rec.zinc_ppm) : "");
    setBoron(rec.boron_ppm !== null && rec.boron_ppm !== undefined ? String(rec.boron_ppm) : "");
    setReviewNotes(rec.review_notes || "");
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
    const objectUrl = URL.createObjectURL(file);
    setInstantPreview({
      url: objectUrl,
      filename: file.name,
      mimeType: file.type || (isPdf ? "application/pdf" : "image/jpeg"),
      kind: isPdf ? "pdf" : "image",
    });
    setUploading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await api.uploadSoilReport(file, sourceType);
      setPendingExtraction(res);
      if (res.record.file_url) {
        setInstantPreview(null);
      }
      populateReviewForm(res.record);
      loadRecords();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const toNumOrNull = (val: string) => (val.trim() === "" ? null : Number(val));

  const handleConfirmReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pendingExtraction) return;
    setConfirming(true);
    setError(null);
    try {
      await api.reviewSoilRecord(pendingExtraction.record.id, {
        ph: toNumOrNull(ph),
        nitrogen_kg_ha: toNumOrNull(nitrogen),
        phosphorus_kg_ha: toNumOrNull(phosphorus),
        potassium_kg_ha: toNumOrNull(potassium),
        organic_carbon_pct: toNumOrNull(oc),
        ec_ds_m: toNumOrNull(ec),
        zinc_ppm: toNumOrNull(zinc),
        boron_ppm: toNumOrNull(boron),
        review_notes: reviewNotes.trim() || null,
      });
      setPendingExtraction(null);
      setSuccess("Verified lab values saved. Lab values override dataset estimates.");
      loadRecords();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save verified values");
    } finally {
      setConfirming(false);
    }
  };

  const handleDatasetEstimate = async (e: React.FormEvent) => {
    e.preventDefault();
    setEstimating(true);
    setError(null);
    setSuccess(null);
    try {
      await api.estimateSoilFromDataset({
        latitude: Number(estLat),
        longitude: Number(estLon),
      });
      setSuccess("Dataset soil estimate recorded (clearly labelled as Estimated).");
      loadRecords();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dataset estimate unavailable");
    } finally {
      setEstimating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-deep">Soil Health & Lab Card OCR</h1>
        <p className="text-sm text-muted mt-1">
          Upload a Soil Health Card or lab report (PDF/JPG/PNG) for OCR extraction and mandatory verification, or look up downloaded Bhuvan/SoilGrids estimates.
        </p>
      </div>

      {success && <SuccessBanner message={success} />}
      {error && <ErrorState message={error} />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* (a) Upload Soil Report */}
        <div className="rm-card p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Upload className="h-5 w-5 text-forest" />
            <h2 className="text-base font-bold text-deep">Upload Lab Report / Soil Health Card</h2>
          </div>

          <div className="flex gap-3 text-xs">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="radio"
                checked={sourceType === "soil_health_card"}
                onChange={() => setSourceType("soil_health_card")}
              />
              Soil Health Card
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="radio"
                checked={sourceType === "lab_report"}
                onChange={() => setSourceType("lab_report")}
              />
              Lab Soil Report
            </label>
          </div>

          <label className="block rounded-2xl border-2 border-dashed border-forest/25 bg-mint/40 p-6 text-center cursor-pointer hover:bg-mint/70 transition-colors">
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileUpload}
              className="sr-only"
              disabled={uploading}
            />
            <TestTube2 className="h-8 w-8 text-forest mx-auto mb-2" />
            <p className="text-sm font-semibold text-deep">
              {uploading ? "Extracting report values..." : "Click to upload PDF, JPG, or PNG (max 10 MB)"}
            </p>
            <p className="text-xs text-muted mt-1">
              Missing parameters are never guessed—you will review every field before saving.
            </p>
          </label>

          {instantPreview && (
            <MediaPreview
              url={instantPreview.url}
              filename={instantPreview.filename}
              mimeType={instantPreview.mimeType}
              kind={instantPreview.kind}
              aspectClass="h-44"
            />
          )}
        </div>

        {/* (b) Downloadable Dataset GPS Estimate */}
        <div className="rm-card p-6 space-y-4">
          <div className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-forest" />
            <h2 className="text-base font-bold text-deep">GPS Estimate (Downloadable Datasets)</h2>
          </div>
          <p className="text-xs text-muted leading-relaxed">
            Reads local downloaded SoilGrids GeoTIFF/CSV or ISRO Bhuvan datasets (never the paused SoilGrids REST API). Estimates carry a confidence tag and are always overridden by verified lab reports.
          </p>
          <form onSubmit={handleDatasetEstimate} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold mb-1">Latitude</label>
                <input
                  type="number"
                  step="any"
                  required
                  value={estLat}
                  onChange={(e) => setEstLat(e.target.value)}
                  placeholder="e.g. 12.5223"
                  className="rm-input"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Longitude</label>
                <input
                  type="number"
                  step="any"
                  required
                  value={estLon}
                  onChange={(e) => setEstLon(e.target.value)}
                  placeholder="e.g. 76.8975"
                  className="rm-input"
                />
              </div>
            </div>
            <button type="submit" disabled={estimating} className="rm-btn-secondary">
              {estimating ? "Checking local dataset..." : "Lookup Dataset Estimate"}
            </button>
          </form>
        </div>
      </div>

      {/* Mandatory Review-and-Correct Screen */}
      {pendingExtraction && (
        <form onSubmit={handleConfirmReview} className="rm-card border-2 border-forest/30 p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-bold text-deep flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-forest" />
                Mandatory Review & Correct Extracted Values
              </h2>
              <p className="text-xs text-muted mt-0.5">{pendingExtraction.ocr_note}</p>
            </div>
            <span className="rounded-full bg-warning/15 text-[#8A5B00] px-3 py-1 text-xs font-semibold">
              Status: {pendingExtraction.ocr_status}
            </span>
          </div>

          {pendingExtraction.record.file_url && (
            <MediaPreview
              url={pendingExtraction.record.file_url}
              filename={pendingExtraction.record.original_filename}
              mimeType={pendingExtraction.record.file_mime_type}
              kind={pendingExtraction.record.file_kind}
              aspectClass="h-52"
            />
          )}

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-semibold mb-1">Soil pH</label>
              <input type="number" step="0.01" className="rm-input" value={ph} onChange={(e) => setPh(e.target.value)} placeholder="Leave blank if untested" />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1">Nitrogen N (kg/ha)</label>
              <input type="number" step="0.1" className="rm-input" value={nitrogen} onChange={(e) => setNitrogen(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1">Phosphorus P (kg/ha)</label>
              <input type="number" step="0.1" className="rm-input" value={phosphorus} onChange={(e) => setPhosphorus(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1">Potassium K (kg/ha)</label>
              <input type="number" step="0.1" className="rm-input" value={potassium} onChange={(e) => setPotassium(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1">Organic Carbon (%)</label>
              <input type="number" step="0.01" className="rm-input" value={oc} onChange={(e) => setOc(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1">EC (dS/m)</label>
              <input type="number" step="0.01" className="rm-input" value={ec} onChange={(e) => setEc(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1">Zinc Zn (ppm)</label>
              <input type="number" step="0.01" className="rm-input" value={zinc} onChange={(e) => setZinc(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1">Boron B (ppm)</label>
              <input type="number" step="0.01" className="rm-input" value={boron} onChange={(e) => setBoron(e.target.value)} />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold mb-1">Lab / Review Notes</label>
            <input className="rm-input" value={reviewNotes} onChange={(e) => setReviewNotes(e.target.value)} placeholder="Optional lab name or notes" />
          </div>

          <button type="submit" disabled={confirming} className="rm-btn-primary">
            {confirming ? "Confirming..." : "Confirm & Verify Soil Record"}
          </button>
        </form>
      )}

      {/* Records List */}
      <div className="space-y-3">
        <h2 className="text-lg font-bold text-deep">Saved Soil Records</h2>
        {loading ? (
          <CardSkeleton lines={4} />
        ) : records.length === 0 ? (
          <EmptyState
            title="No soil records yet"
            description="Upload a Soil Health Card or lab report above to personalize crop and fertilizer advice."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {records.map((rec) => {
              const isEst = rec.source_type === "dataset_estimate";
              return (
                <div key={rec.id} className="rm-card p-5 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span
                        className={`inline-block rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase ${
                          isEst
                            ? "bg-warning/20 text-[#8A5B00]"
                            : rec.status === "verified"
                            ? "bg-mint text-forest"
                            : "bg-cream text-muted"
                        }`}
                      >
                        {isEst
                          ? `ESTIMATED (${rec.confidence_level})`
                          : `${rec.source_type.replace("_", " ")} • ${rec.status}`}
                      </span>
                      <p className="text-sm font-semibold text-ink mt-1.5">
                        {rec.original_filename || rec.dataset_name || "Soil Record"}
                      </p>
                    </div>
                    {rec.status === "pending_review" && (
                      <button
                        type="button"
                        onClick={() => {
                          setPendingExtraction({
                            record: rec,
                            ocr_status: "pending_review",
                            ocr_note: "Review extracted values below and confirm.",
                            requires_review: true,
                          });
                          populateReviewForm(rec);
                        }}
                        className="rm-btn-secondary text-xs px-3 py-1.5"
                      >
                        Review Now
                      </button>
                    )}
                  </div>

                  {rec.file_url && (
                    <MediaPreview
                      url={rec.file_url}
                      filename={rec.original_filename}
                      mimeType={rec.file_mime_type}
                      kind={rec.file_kind}
                      aspectClass="h-44"
                      compact
                    />
                  )}

                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="rounded-xl bg-cream p-2">
                      <span className="text-muted">pH</span>
                      <p className="font-bold text-deep">{rec.ph ?? "Not tested"}</p>
                    </div>
                    <div className="rounded-xl bg-cream p-2">
                      <span className="text-muted">N (kg/ha)</span>
                      <p className="font-bold text-deep">{rec.nitrogen_kg_ha ?? "Not tested"}</p>
                    </div>
                    <div className="rounded-xl bg-cream p-2">
                      <span className="text-muted">P (kg/ha)</span>
                      <p className="font-bold text-deep">{rec.phosphorus_kg_ha ?? "Not tested"}</p>
                    </div>
                    <div className="rounded-xl bg-cream p-2">
                      <span className="text-muted">K (kg/ha)</span>
                      <p className="font-bold text-deep">{rec.potassium_kg_ha ?? "Not tested"}</p>
                    </div>
                    <div className="rounded-xl bg-cream p-2">
                      <span className="text-muted">OC (%)</span>
                      <p className="font-bold text-deep">{rec.organic_carbon_pct ?? "Not tested"}</p>
                    </div>
                    <div className="rounded-xl bg-cream p-2">
                      <span className="text-muted">EC (dS/m)</span>
                      <p className="font-bold text-deep">{rec.ec_ds_m ?? "Not tested"}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

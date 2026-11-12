import React, { useEffect, useState } from "react";
import { CalendarCheck, Plus, Trash2, CheckSquare, Square } from "lucide-react";
import {
  CardSkeleton,
  EmptyState,
  ErrorState,
  SuccessBanner,
} from "@/components/common/StateFeedback";
import { api } from "@/services/api";
import type { TrackedCrop } from "@/types";

const STAGES = ["germination", "vegetative", "flowering", "fruiting", "maturity"];

export const CropMonitoringPage: React.FC = () => {
  const [crops, setCrops] = useState<TrackedCrop[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Add form
  const [cropName, setCropName] = useState("");
  const [variety, setVariety] = useState("");
  const [category, setCategory] = useState("cereal");
  const [sowingDate, setSowingDate] = useState(new Date().toISOString().slice(0, 10));
  const [acreage, setAcreage] = useState("1.5");
  const [irrigationType, setIrrigationType] = useState("drip");
  const [adding, setAdding] = useState(false);

  const loadCrops = () => {
    setLoading(true);
    api
      .getTrackedCrops()
      .then(setCrops)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load crops"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadCrops();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdding(true);
    setError(null);
    setSuccess(null);
    try {
      await api.createTrackedCrop({
        crop_name: cropName,
        variety: variety.trim() || null,
        category,
        sowing_date: sowingDate,
        acreage: Number(acreage) || 1,
        irrigation_type: irrigationType,
      });
      setCropName("");
      setVariety("");
      setSuccess("Crop added to growth stage monitoring.");
      loadCrops();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add crop");
    } finally {
      setAdding(false);
    }
  };

  const handleToggleTask = async (crop: TrackedCrop, task: string) => {
    const exists = crop.completed_tasks.includes(task);
    const updatedTasks = exists
      ? crop.completed_tasks.filter((t) => t !== task)
      : [...crop.completed_tasks, task];
    try {
      const updated = await api.updateTrackedCrop(crop.id, { completed_tasks: updatedTasks });
      setCrops((prev) => prev.map((c) => (c.id === crop.id ? updated : c)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update task");
    }
  };

  const handleStageChange = async (crop: TrackedCrop, newStage: string) => {
    try {
      const updated = await api.updateTrackedCrop(crop.id, { current_stage: newStage });
      setCrops((prev) => prev.map((c) => (c.id === crop.id ? updated : c)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update stage");
    }
  };

  const handleDelete = async (cropId: number) => {
    try {
      await api.deleteTrackedCrop(cropId);
      setCrops((prev) => prev.filter((c) => c.id !== cropId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete crop");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-deep">Crop Growth Monitoring</h1>
        <p className="text-sm text-muted mt-1">
          Stage-wise irrigation, nutrient, and cultivation task checklists tailored to your sowing date.
        </p>
      </div>

      {success && <SuccessBanner message={success} />}
      {error && <ErrorState message={error} />}

      <form onSubmit={handleAdd} className="rm-card p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 items-end">
        <div>
          <label className="block text-xs font-semibold mb-1">Crop Name *</label>
          <input
            required
            className="rm-input"
            value={cropName}
            onChange={(e) => setCropName(e.target.value)}
            placeholder="e.g. Tomato"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Variety</label>
          <input
            className="rm-input"
            value={variety}
            onChange={(e) => setVariety(e.target.value)}
            placeholder="e.g. Arka Rakshak"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Category</label>
          <select className="rm-input" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="cereal">Cereal / Millet</option>
            <option value="pulse">Pulse</option>
            <option value="oilseed">Oilseed</option>
            <option value="vegetable">Vegetable</option>
            <option value="fruit">Fruit</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Sowing Date *</label>
          <input
            type="date"
            required
            className="rm-input"
            value={sowingDate}
            onChange={(e) => setSowingDate(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Acres & Irrigation</label>
          <div className="flex gap-2">
            <input
              type="number"
              step="0.1"
              min="0.1"
              className="rm-input w-20"
              value={acreage}
              onChange={(e) => setAcreage(e.target.value)}
            />
            <select
              className="rm-input"
              value={irrigationType}
              onChange={(e) => setIrrigationType(e.target.value)}
            >
              <option value="drip">Drip</option>
              <option value="furrow">Furrow</option>
              <option value="rainfed">Rainfed</option>
              <option value="sprinkler">Sprinkler</option>
            </select>
          </div>
        </div>
        <button type="submit" disabled={adding} className="rm-btn-primary">
          <Plus className="h-4 w-4" />
          {adding ? "Adding..." : "Track Crop"}
        </button>
      </form>

      {loading ? (
        <CardSkeleton lines={5} />
      ) : crops.length === 0 ? (
        <EmptyState
          title="No tracked crops yet"
          description="Add a sown crop above to get stage-wise irrigation, fertilizer, and field care tasks."
        />
      ) : (
        <div className="space-y-4">
          {crops.map((crop) => (
            <div key={crop.id} className="rm-card p-6 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <CalendarCheck className="h-5 w-5 text-forest" />
                    <h2 className="text-lg font-bold text-deep">
                      {crop.crop_name} {crop.variety ? `(${crop.variety})` : ""}
                    </h2>
                  </div>
                  <p className="text-xs text-muted mt-1">
                    Sown {crop.sowing_date} • Day {crop.days_since_sowing} • {crop.acreage} acres •{" "}
                    {crop.irrigation_type}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <select
                    aria-label="Update crop growth stage"
                    value={crop.current_stage}
                    onChange={(e) => void handleStageChange(crop, e.target.value)}
                    className="rm-input w-40 text-xs font-semibold"
                  >
                    {STAGES.map((st) => (
                      <option key={st} value={st}>
                        Stage: {st.charAt(0).toUpperCase() + st.slice(1)}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => void handleDelete(crop.id)}
                    className="p-2 rounded-xl border border-danger/25 text-danger hover:bg-danger/10"
                    aria-label="Remove tracked crop"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {crop.stage_guidance && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  <div className="rm-surface p-4 text-xs space-y-1.5">
                    <p className="font-bold text-deep">
                      {crop.stage_guidance.stage_label} ({crop.stage_guidance.day_range})
                    </p>
                    <p className="text-ink/90">
                      <strong>Irrigation:</strong> {crop.stage_guidance.irrigation_advice}
                    </p>
                    <p className="text-ink/90">
                      <strong>Nutrients:</strong> {crop.stage_guidance.nutrient_advice}
                    </p>
                  </div>

                  <div className="lg:col-span-2 rounded-2xl border border-[#176B35]/10 bg-cream p-4 space-y-2">
                    <p className="text-xs font-bold text-deep">Cultivation Checklist</p>
                    <div className="space-y-2">
                      {crop.stage_guidance.cultivation_tasks.map((task) => {
                        const done = crop.completed_tasks.includes(task);
                        return (
                          <button
                            key={task}
                            type="button"
                            onClick={() => void handleToggleTask(crop, task)}
                            className="w-full flex items-start gap-2.5 text-left text-xs hover:text-forest transition-colors"
                          >
                            {done ? (
                              <CheckSquare className="h-4 w-4 text-forest shrink-0 mt-0.5" />
                            ) : (
                              <Square className="h-4 w-4 text-muted shrink-0 mt-0.5" />
                            )}
                            <span className={done ? "line-through text-muted" : "text-ink"}>
                              {task}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

import React, { useEffect, useState } from "react";
import { MapPin, Save, Settings2 } from "lucide-react";
import {
  CardSkeleton,
  ErrorState,
  IntegrationStatusBadge,
  SuccessBanner,
} from "@/components/common/StateFeedback";
import { useAuth } from "@/context/AuthContext";
import { SUPPORTED_LANGUAGES, useLanguage } from "@/context/LanguageContext";
import { api } from "@/services/api";
import type { IntegrationStatusItem, LanguageCode } from "@/types";

export const ProfilePage: React.FC = () => {
  const { farmer, updateProfile } = useAuth();
  const { setLanguage } = useLanguage();

  const [fullName, setFullName] = useState(farmer?.full_name || "");
  const [email, setEmail] = useState(farmer?.email || "");
  const [stateName, setStateName] = useState(farmer?.state || "");
  const [district, setDistrict] = useState(farmer?.district || "");
  const [village, setVillage] = useState(farmer?.village || "");
  const [farmSize, setFarmSize] = useState(String(farmer?.farm_size_acres || 2));
  const [soilType, setSoilType] = useState(farmer?.soil_type || "");
  const [mainCrops, setMainCrops] = useState((farmer?.main_crops || []).join(", "));
  const [preferredLang, setPreferredLang] = useState<LanguageCode>(
    (farmer?.preferred_language as LanguageCode) || "kn-IN"
  );
  const [farmerCategory, setFarmerCategory] = useState(farmer?.farmer_category || "small");
  const [gpsConsent, setGpsConsent] = useState(Boolean(farmer?.gps_consent));
  const [latitude, setLatitude] = useState<string>(
    farmer?.latitude !== null && farmer?.latitude !== undefined ? String(farmer.latitude) : ""
  );
  const [longitude, setLongitude] = useState<string>(
    farmer?.longitude !== null && farmer?.longitude !== undefined ? String(farmer.longitude) : ""
  );

  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [integrations, setIntegrations] = useState<Record<string, IntegrationStatusItem> | null>(
    null
  );
  const [loadingIntegrations, setLoadingIntegrations] = useState(true);

  useEffect(() => {
    api
      .getIntegrationStatuses()
      .then((res) => setIntegrations(res.integrations))
      .catch(() => setIntegrations(null))
      .finally(() => setLoadingIntegrations(false));
  }, []);

  const handleGpsCapture = () => {
    if (!gpsConsent || !navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((pos) => {
      setLatitude(pos.coords.latitude.toFixed(5));
      setLongitude(pos.coords.longitude.toFixed(5));
    });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaveMessage(null);
    try {
      const updated = await updateProfile({
        full_name: fullName,
        email: email.trim() || null,
        state: stateName,
        district,
        village,
        farm_size_acres: Number(farmSize) || 1,
        soil_type: soilType.trim() || null,
        main_crops: mainCrops
          .split(",")
          .map((c) => c.trim())
          .filter(Boolean),
        preferred_language: preferredLang,
        farmer_category: farmerCategory,
        gps_consent: gpsConsent,
        latitude: gpsConsent && latitude ? Number(latitude) : null,
        longitude: gpsConsent && longitude ? Number(longitude) : null,
      });
      setLanguage((updated.preferred_language as LanguageCode) || "en-IN");
      setSaveMessage("Farmer profile and preferences saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-deep">Farmer Profile & Settings</h1>
        <p className="text-sm text-muted mt-1">
          Manage your farm location, crops, preferred voice language, and inspect live API status.
        </p>
      </div>

      {saveMessage && <SuccessBanner message={saveMessage} />}
      {error && <ErrorState message={error} />}

      <form onSubmit={handleSave} className="rm-card p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold mb-1.5">Full Name</label>
            <input className="rm-input" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1.5">Mobile (Registered)</label>
            <input className="rm-input bg-cream" value={farmer?.mobile || ""} disabled />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1.5">Email</label>
            <input className="rm-input" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1.5">State</label>
            <input className="rm-input" value={stateName} onChange={(e) => setStateName(e.target.value)} required />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1.5">District</label>
            <input className="rm-input" value={district} onChange={(e) => setDistrict(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1.5">Village</label>
            <input className="rm-input" value={village} onChange={(e) => setVillage(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1.5">Farm Size (Acres)</label>
            <input
              type="number"
              step="0.1"
              min="0.1"
              className="rm-input"
              value={farmSize}
              onChange={(e) => setFarmSize(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1.5">Soil Type (Optional)</label>
            <input className="rm-input" value={soilType} onChange={(e) => setSoilType(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1.5">Farmer Category</label>
            <select
              className="rm-input"
              value={farmerCategory}
              onChange={(e) => setFarmerCategory(e.target.value)}
            >
              <option value="marginal">Marginal</option>
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className="block text-xs font-semibold mb-1.5">Main Crops (comma-separated)</label>
            <input className="rm-input" value={mainCrops} onChange={(e) => setMainCrops(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1.5">Preferred Language</label>
            <select
              className="rm-input"
              value={preferredLang}
              onChange={(e) => setPreferredLang(e.target.value as LanguageCode)}
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.nativeName} ({lang.name})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="rm-surface p-4 space-y-3">
          <label className="flex items-start gap-2.5 text-xs text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={gpsConsent}
              onChange={(e) => {
                setGpsConsent(e.target.checked);
                if (!e.target.checked) {
                  setLatitude("");
                  setLongitude("");
                }
              }}
              className="mt-0.5 rounded border-forest text-forest"
            />
            <span>
              <strong>Opt-in GPS Location:</strong> Allow storing latitude/longitude for weather and
              soil dataset lookups. Revoking clears saved GPS coordinates.
            </span>
          </label>
          {gpsConsent && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
              <div>
                <label className="block text-xs font-semibold mb-1">Latitude</label>
                <input
                  className="rm-input"
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                  placeholder="e.g. 12.5223"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Longitude</label>
                <input
                  className="rm-input"
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                  placeholder="e.g. 76.8975"
                />
              </div>
              <button type="button" onClick={handleGpsCapture} className="rm-btn-secondary">
                <MapPin className="h-4 w-4" />
                Use Browser GPS
              </button>
            </div>
          )}
        </div>

        <button type="submit" disabled={saving} className="rm-btn-primary">
          <Save className="h-4 w-4" />
          {saving ? "Saving..." : "Save Profile"}
        </button>
      </form>

      {/* Honest Integration Status Panel */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Settings2 className="h-5 w-5 text-forest" />
          <h2 className="text-lg font-bold text-deep">External Integration Status</h2>
        </div>
        {loadingIntegrations ? (
          <CardSkeleton lines={4} />
        ) : integrations ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(integrations).map(([key, item]) => (
              <div key={key} className="rm-card p-4 flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-ink">{item.name}</p>
                  <p className="text-xs text-muted mt-1">{item.note}</p>
                </div>
                <IntegrationStatusBadge status={item.status} />
              </div>
            ))}
          </div>
        ) : (
          <ErrorState message="Could not load integration status." />
        )}
      </div>
    </div>
  );
};

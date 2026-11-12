import React, { useEffect, useState } from "react";
import { Camera, Save, Settings2, Upload } from "lucide-react";
import { FarmLocationPicker, type FarmLocationValue } from "@/components/common/FarmLocationPicker";
import { MediaPreview } from "@/components/common/MediaPreview";
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
  const { farmer, updateProfile, refreshProfile } = useAuth();
  const { setLanguage } = useLanguage();

  const [fullName, setFullName] = useState(farmer?.full_name || "");
  const [email, setEmail] = useState(farmer?.email || "");
  const [location, setLocation] = useState<FarmLocationValue>({
    state: farmer?.state || "",
    district: farmer?.district || "",
    taluk: farmer?.taluk || "",
    village: farmer?.village || "",
    location_address: farmer?.location_address || null,
    latitude: farmer?.latitude ?? null,
    longitude: farmer?.longitude ?? null,
    gps_consent: Boolean(farmer?.gps_consent),
    continuous_gps_opt_in: Boolean(farmer?.continuous_gps_opt_in),
    location_source: (farmer?.location_source as "gps" | "gps_corrected" | "manual") || "manual",
  });
  const [farmSize, setFarmSize] = useState(String(farmer?.farm_size_acres || 2));
  const [soilType, setSoilType] = useState(farmer?.soil_type || "");
  const [mainCrops, setMainCrops] = useState((farmer?.main_crops || []).join(", "));
  const [preferredLang, setPreferredLang] = useState<LanguageCode>(
    (farmer?.preferred_language as LanguageCode) || "kn-IN"
  );
  const [farmerCategory, setFarmerCategory] = useState(farmer?.farmer_category || "small");

  const [avatarPreviewUrl, setAvatarPreviewUrl] = useState<string | null>(farmer?.avatar_url || null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [integrations, setIntegrations] = useState<Record<string, IntegrationStatusItem> | null>(
    null
  );
  const [loadingIntegrations, setLoadingIntegrations] = useState(true);

  useEffect(() => {
    if (farmer?.avatar_url) {
      setAvatarPreviewUrl(farmer.avatar_url);
    }
  }, [farmer?.avatar_url]);

  useEffect(() => {
    api
      .getIntegrationStatuses()
      .then((res) => setIntegrations(res.integrations))
      .catch(() => setIntegrations(null))
      .finally(() => setLoadingIntegrations(false));
  }, []);

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setSaveMessage(null);
    // Show instant local preview while persistent signed URL saves on server
    const tempObjectUrl = URL.createObjectURL(file);
    setAvatarPreviewUrl(tempObjectUrl);
    setUploadingPhoto(true);
    try {
      const updated = await api.uploadProfilePhoto(file);
      setAvatarPreviewUrl(updated.avatar_url || tempObjectUrl);
      await refreshProfile();
      setSaveMessage("Profile photograph uploaded and saved permanently.");
    } catch (err) {
      setAvatarPreviewUrl(farmer?.avatar_url || null);
      setError(err instanceof Error ? err.message : "Failed to upload profile photo.");
    } finally {
      setUploadingPhoto(false);
      e.target.value = "";
    }
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
        state: location.state,
        district: location.district,
        taluk: location.taluk,
        village: location.village,
        location_address: location.location_address || null,
        location_source: location.gps_consent && location.latitude != null ? location.location_source : "manual",
        farm_size_acres: Number(farmSize) || 1,
        soil_type: soilType.trim() || null,
        main_crops: mainCrops
          .split(",")
          .map((c) => c.trim())
          .filter(Boolean),
        preferred_language: preferredLang,
        farmer_category: farmerCategory,
        gps_consent: location.gps_consent,
        continuous_gps_opt_in: location.gps_consent ? location.continuous_gps_opt_in : false,
        latitude: location.gps_consent ? location.latitude : null,
        longitude: location.gps_consent ? location.longitude : null,
      });
      await api.verifyLocation({
        state: location.state,
        district: location.district,
        taluk: location.taluk,
        village: location.village,
        location_address: location.location_address || null,
        location_source: location.gps_consent && location.latitude != null ? location.location_source : "manual",
        gps_consent: location.gps_consent,
        continuous_gps_opt_in: location.gps_consent ? location.continuous_gps_opt_in : false,
        latitude: location.gps_consent ? location.latitude : null,
        longitude: location.gps_consent ? location.longitude : null,
      });
      setLanguage((updated.preferred_language as LanguageCode) || "en-IN");
      setSaveMessage("Farmer profile, verified GPS location, and preferences saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-deep">Farmer Profile, Photo & Live GPS Location</h1>
        <p className="text-sm text-muted mt-1">
          Verify your farm GPS coordinates on the map, upload your profile photo, and configure language preferences.
        </p>
      </div>

      {saveMessage && <SuccessBanner message={saveMessage} />}
      {error && <ErrorState message={error} />}

      {/* Farmer Profile Photograph Upload & Persistent Preview */}
      <div className="rm-card p-6 grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        <div className="md:col-span-2 space-y-2">
          <div className="flex items-center gap-2 text-deep font-semibold text-sm">
            <Camera className="h-4 w-4 text-forest" />
            <span>Farmer Profile Photograph</span>
          </div>
          <p className="text-xs text-muted">
            Upload your photo (JPG, PNG, WEBP up to 10 MB). Stored securely and remains visible across refreshes and sessions.
          </p>
          <label className="rm-btn-secondary inline-flex cursor-pointer text-xs mt-1">
            <Upload className="h-3.5 w-3.5" />
            {uploadingPhoto ? "Uploading Photo..." : "Upload Profile Photo"}
            <input
              type="file"
              accept=".jpg,.jpeg,.png,.webp"
              onChange={handleAvatarUpload}
              disabled={uploadingPhoto}
              className="hidden"
            />
          </label>
        </div>

        <div>
          {avatarPreviewUrl ? (
            <MediaPreview
              url={avatarPreviewUrl}
              filename={`${farmer?.full_name || "Farmer"} Photo`}
              kind="image"
              aspectClass="h-40"
            />
          ) : (
            <div className="h-36 rounded-xl border border-dashed border-[#CFE4C8] bg-[#FAF9F2] flex flex-col items-center justify-center text-xs text-muted">
              <Camera className="h-6 w-6 text-forest/50 mb-1" />
              <span>No profile photo uploaded</span>
            </div>
          )}
        </div>
      </div>

      <form onSubmit={handleSave} className="rm-card p-6 space-y-6">
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

        {/* Interactive Live GPS Detection, Reverse Geocoding & Map Pin Override */}
        <FarmLocationPicker value={location} onChange={setLocation} allowAuthReverse={true} />

        <button type="submit" disabled={saving} className="rm-btn-primary">
          <Save className="h-4 w-4" />
          {saving ? "Saving..." : "Save Profile & Verified Location"}
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
        ) : null}
      </div>
    </div>
  );
};

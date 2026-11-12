import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Shield, Sprout } from "lucide-react";
import { BrandLogo } from "@/components/common/BrandLogo";
import { FarmLocationPicker, type FarmLocationValue } from "@/components/common/FarmLocationPicker";
import { ErrorState } from "@/components/common/StateFeedback";
import { useAuth } from "@/context/AuthContext";
import { SUPPORTED_LANGUAGES, useLanguage } from "@/context/LanguageContext";
import type { LanguageCode } from "@/types";

export const AuthPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialMode = searchParams.get("mode") === "register" ? "register" : "login";
  const [mode, setMode] = useState<"login" | "register">(initialMode);

  const { login, register } = useAuth();
  const { setLanguage } = useLanguage();
  const navigate = useNavigate();

  // Login fields
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");

  // Register fields
  const [fullName, setFullName] = useState("");
  const [mobile, setMobile] = useState("");
  const [email, setEmail] = useState("");
  const [location, setLocation] = useState<FarmLocationValue>({
    state: "Karnataka",
    district: "",
    taluk: "",
    village: "",
    location_address: null,
    latitude: null,
    longitude: null,
    gps_consent: false,
    continuous_gps_opt_in: false,
    location_source: "manual",
  });
  const [farmSize, setFarmSize] = useState("2.5");
  const [soilType, setSoilType] = useState("");
  const [mainCropsText, setMainCropsText] = useState("Ragi, Tomato");
  const [preferredLanguage, setPreferredLanguage] = useState<LanguageCode>("kn-IN");
  const [farmerCategory, setFarmerCategory] = useState("small");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "login") {
        const farmer = await login(identifier, password);
        setLanguage((farmer.preferred_language as LanguageCode) || "en-IN");
      } else {
        const crops = mainCropsText
          .split(",")
          .map((c) => c.trim())
          .filter(Boolean);
        const farmer = await register({
          full_name: fullName,
          mobile,
          email: email.trim() || null,
          password,
          state: location.state,
          district: location.district,
          taluk: location.taluk,
          village: location.village,
          location_address: location.location_address || null,
          location_source: location.gps_consent && location.latitude != null ? location.location_source : "manual",
          latitude: location.gps_consent ? location.latitude : null,
          longitude: location.gps_consent ? location.longitude : null,
          gps_consent: location.gps_consent,
          continuous_gps_opt_in: location.gps_consent ? location.continuous_gps_opt_in : false,
          farm_size_acres: Number(farmSize) || 1.0,
          soil_type: soilType.trim() || null,
          main_crops: crops,
          preferred_language: preferredLanguage,
          farmer_category: farmerCategory,
        });
        setLanguage((farmer.preferred_language as LanguageCode) || "en-IN");
      }
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream flex flex-col justify-center py-8 px-4 sm:px-6">
      <div className={`${mode === "register" ? "max-w-3xl" : "max-w-xl"} w-full mx-auto space-y-6`}>
        <div className="flex items-center justify-between">
          <Link to="/">
            <BrandLogo size="md" />
          </Link>
          <div className="inline-flex rounded-xl bg-white p-1 border border-[#176B35]/15">
            <button
              type="button"
              onClick={() => {
                setMode("login");
                setError(null);
              }}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                mode === "login" ? "bg-forest text-white" : "text-muted hover:text-ink"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("register");
                setError(null);
              }}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                mode === "register" ? "bg-forest text-white" : "text-muted hover:text-ink"
              }`}
            >
              Register
            </button>
          </div>
        </div>

        <div className="rm-card p-6 sm:p-8 space-y-5">
          <div>
            <h1 className="text-2xl font-bold text-deep">
              {mode === "login" ? "Welcome Back, Farmer" : "Create Your Farmer Profile"}
            </h1>
            <p className="text-sm text-muted mt-1">
              {mode === "login"
                ? "Sign in with your registered mobile number or email."
                : "Your profile personalizes voice answers, weather, soil, and scheme matches."}
            </p>
          </div>

          {error && <ErrorState message={error} />}

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "login" ? (
              <>
                <div>
                  <label className="block text-xs font-semibold text-ink mb-1.5">
                    Mobile Number or Email
                  </label>
                  <input
                    type="text"
                    required
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    placeholder="e.g. 9876543210 or farmer@example.com"
                    className="rm-input"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-ink mb-1.5">Password</label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="rm-input"
                  />
                </div>
              </>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-ink mb-1.5">Full Name *</label>
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Basavaraj Gowda"
                      className="rm-input"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-ink mb-1.5">Mobile Number *</label>
                    <input
                      type="tel"
                      required
                      value={mobile}
                      onChange={(e) => setMobile(e.target.value)}
                      placeholder="10-digit mobile"
                      className="rm-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-ink mb-1.5">
                      Email (Optional)
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="farmer@example.com"
                      className="rm-input"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-ink mb-1.5">
                      Password (min 8 chars) *
                    </label>
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Create a strong password"
                      className="rm-input"
                    />
                  </div>
                </div>

                <FarmLocationPicker
                  value={location}
                  onChange={setLocation}
                  allowAuthReverse={false}
                  compactMapHeight="h-44"
                />

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-ink mb-1.5">
                      Farm Size (Acres)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      value={farmSize}
                      onChange={(e) => setFarmSize(e.target.value)}
                      className="rm-input"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-ink mb-1.5">
                      Soil Type (Optional)
                    </label>
                    <input
                      type="text"
                      value={soilType}
                      onChange={(e) => setSoilType(e.target.value)}
                      placeholder="e.g. Red Loam"
                      className="rm-input"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-ink mb-1.5">
                      Farmer Category
                    </label>
                    <select
                      value={farmerCategory}
                      onChange={(e) => setFarmerCategory(e.target.value)}
                      className="rm-input"
                    >
                      <option value="marginal">Marginal (&lt; 2.5 ac)</option>
                      <option value="small">Small (2.5 - 5 ac)</option>
                      <option value="medium">Medium (5 - 25 ac)</option>
                      <option value="large">Large (&gt; 25 ac)</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-ink mb-1.5">
                      Main Crops (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={mainCropsText}
                      onChange={(e) => setMainCropsText(e.target.value)}
                      placeholder="Ragi, Tomato, Paddy"
                      className="rm-input"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-ink mb-1.5">
                      Preferred Language
                    </label>
                    <select
                      value={preferredLanguage}
                      onChange={(e) => setPreferredLanguage(e.target.value as LanguageCode)}
                      className="rm-input"
                    >
                      {SUPPORTED_LANGUAGES.map((lang) => (
                        <option key={lang.code} value={lang.code}>
                          {lang.nativeName} ({lang.name})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

              </>
            )}

            <button type="submit" disabled={submitting} className="rm-btn-primary w-full py-3">
              <Sprout className="h-4 w-4" />
              {submitting
                ? "Please wait..."
                : mode === "login"
                ? "Sign In to Raitha Mitra"
                : "Create Farmer Account"}
            </button>
          </form>

          <div className="flex items-center gap-2 text-[11px] text-muted pt-1">
            <Shield className="h-3.5 w-3.5 text-forest shrink-0" />
            <span>Your farm data is private and protected by per-farmer JWT authorization.</span>
          </div>
        </div>
      </div>
    </div>
  );
};

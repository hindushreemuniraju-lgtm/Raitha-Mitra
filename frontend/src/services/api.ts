const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";
const TOKEN_STORAGE_KEY = "raitha_mitra_token";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  isMultipart = false
): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers || {});

  if (!isMultipart && !headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const errBody = await response.json();
      if (typeof errBody?.detail === "string") {
        detail = errBody.detail;
      } else if (Array.isArray(errBody?.detail)) {
        detail = errBody.detail.map((item: { msg?: string }) => item.msg || JSON.stringify(item)).join("; ");
      }
    } catch {
      // Ignore JSON parse failures on non-JSON errors
    }
    if (response.status === 401) {
      setStoredToken(null);
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  // System
  getHealth: () => request<{ status: string; app: string; environment: string }>("/health"),
  getIntegrationStatuses: () =>
    request<{ integrations: Record<string, import("@/types").IntegrationStatusItem> }>("/integrations/status"),

  // Auth & Profile
  register: (payload: Record<string, unknown>) =>
    request<import("@/types").TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  login: (payload: { identifier: string; password: string }) =>
    request<import("@/types").TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getMyProfile: () => request<import("@/types").FarmerProfile>("/farmers/me"),
  updateMyProfile: (payload: Record<string, unknown>) =>
    request<import("@/types").FarmerProfile>("/farmers/me", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  uploadProfilePhoto: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<import("@/types").FarmerProfile>(
      "/farmers/me/photo",
      { method: "POST", body: form },
      true
    );
  },

  // Live GPS Location & Reverse Geocoding
  reverseGeocode: (lat: number, lon: number) =>
    request<import("@/types").ReverseGeocodeResult>(`/location/reverse?lat=${lat}&lon=${lon}`),
  verifyLocation: (payload: {
    latitude?: number | null;
    longitude?: number | null;
    gps_consent: boolean;
    continuous_gps_opt_in: boolean;
    state: string;
    district: string;
    taluk: string;
    village: string;
    location_address?: string | null;
    location_source: "gps" | "gps_corrected" | "manual";
  }) =>
    request<import("@/types").FarmerProfile>("/location/verify", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Dashboard
  getDashboard: () => request<import("@/types").DashboardSummary>("/dashboard"),

  // Weather & Flood
  getWeather: (params?: { state?: string; district?: string; lat?: number; lon?: number }) => {
    const qs = new URLSearchParams();
    if (params?.state) qs.set("state", params.state);
    if (params?.district) qs.set("district", params.district);
    if (params?.lat !== undefined) qs.set("lat", String(params.lat));
    if (params?.lon !== undefined) qs.set("lon", String(params.lon));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<import("@/types").WeatherFloodResponse>(`/weather${suffix}`);
  },

  // Soil Health
  getSoilRecords: () => request<import("@/types").SoilRecord[]>("/soil/records"),
  uploadSoilReport: (file: File, sourceType: "lab_report" | "soil_health_card") => {
    const form = new FormData();
    form.append("file", file);
    form.append("source_type", sourceType);
    return request<import("@/types").SoilUploadExtraction>(
      "/soil/upload",
      { method: "POST", body: form },
      true
    );
  },
  reviewSoilRecord: (recordId: number, payload: Record<string, unknown>) =>
    request<import("@/types").SoilRecord>(`/soil/records/${recordId}/review`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  estimateSoilFromDataset: (payload: { latitude: number; longitude: number; dataset_preference?: string }) =>
    request<import("@/types").SoilRecord>("/soil/estimate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Crop Recommendation & Growth Monitoring
  recommendCrops: (payload: Record<string, unknown>) =>
    request<import("@/types").CropRecommendationResponse>("/crops/recommend", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getTrackedCrops: () => request<import("@/types").TrackedCrop[]>("/crops/monitoring"),
  createTrackedCrop: (payload: Record<string, unknown>) =>
    request<import("@/types").TrackedCrop>("/crops/monitoring", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateTrackedCrop: (cropId: number, payload: Record<string, unknown>) =>
    request<import("@/types").TrackedCrop>(`/crops/monitoring/${cropId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteTrackedCrop: (cropId: number) =>
    request<void>(`/crops/monitoring/${cropId}`, { method: "DELETE" }),
  uploadCropPhoto: (cropId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<import("@/types").TrackedCrop>(
      `/crops/monitoring/${cropId}/photo`,
      { method: "POST", body: form },
      true
    );
  },

  // Harvest Protection & Profit Optimization
  getHarvestProtection: () =>
    request<import("@/types").HarvestProtectionSummary>("/harvest/protection"),
  analyzeHarvest: (payload: {
    crop_name: string;
    variety?: string;
    sowing_date: string;
    current_stage: string;
    acreage: number;
    irrigation_type: string;
  }) =>
    request<import("@/types").HarvestProtectionDecision>("/harvest/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Smart Notifications & Monitoring
  getNotifications: (limit = 50) =>
    request<import("@/types").NotificationList>(`/notifications?limit=${limit}`),
  checkMonitoringNow: () =>
    request<import("@/types").NotificationList>("/notifications/check-now", {
      method: "POST",
    }),
  markNotificationRead: (notificationId: number) =>
    request<import("@/types").NotificationItem>(`/notifications/${notificationId}/read`, {
      method: "POST",
    }),
  markAllNotificationsRead: () =>
    request<{ marked_read: number }>("/notifications/read-all", {
      method: "POST",
    }),

  // Pest & Disease Detection
  getDiseaseScans: () => request<import("@/types").DiseaseScan[]>("/pests/scans"),
  analyzeDiseaseImage: (file: File, cropName?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (cropName) form.append("crop_name", cropName);
    return request<import("@/types").DiseaseScan>(
      "/pests/analyze",
      { method: "POST", body: form },
      true
    );
  },

  // Fertilizer
  recommendFertilizer: (payload: Record<string, unknown>) =>
    request<import("@/types").FertilizerResponse>("/fertilizer/recommend", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Yield & Harvest
  predictYield: (payload: Record<string, unknown>) =>
    request<import("@/types").YieldPredictionResponse>("/yield/predict", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Nutrition & Utilization
  getNutrition: (query: string) =>
    request<import("@/types").NutritionResponse>(`/nutrition?query=${encodeURIComponent(query)}`),

  // Mandi Prices
  getMandiPrices: (params: {
    commodity?: string;
    state?: string;
    district?: string;
    market?: string;
    date?: string;
    include_demo?: boolean;
  }) => {
    const qs = new URLSearchParams();
    if (params.commodity) qs.set("commodity", params.commodity);
    if (params.state) qs.set("state", params.state);
    if (params.district) qs.set("district", params.district);
    if (params.market) qs.set("market", params.market);
    if (params.date) qs.set("date", params.date);
    if (params.include_demo) qs.set("include_demo", "true");
    return request<import("@/types").MandiResponse>(`/mandi?${qs.toString()}`);
  },

  // Profit Calculator
  calculateProfit: (payload: import("@/types").ProfitCalculateRequest) =>
    request<import("@/types").ProfitScenarioResult>("/profit/calculate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getProfitScenarios: () => request<import("@/types").ProfitScenarioResult[]>("/profit/scenarios"),

  // Government Schemes
  getSchemes: (params: { state?: string; district?: string; category?: string; crop?: string }) => {
    const qs = new URLSearchParams();
    if (params.state) qs.set("state", params.state);
    if (params.district) qs.set("district", params.district);
    if (params.category) qs.set("category", params.category);
    if (params.crop) qs.set("crop", params.crop);
    return request<import("@/types").SchemesResponse>(`/schemes?${qs.toString()}`);
  },

  // Voice Assistant
  getVoiceSessions: () => request<import("@/types").VoiceSession[]>("/voice/sessions"),
  getVoiceMessages: (sessionId: number) =>
    request<import("@/types").VoiceMessage[]>(`/voice/sessions/${sessionId}/messages`),
  createLiveKitToken: (payload: { language_code: string; session_id?: number }) =>
    request<import("@/types").VoiceTokenResponse>("/voice/token", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  sendVoiceTextTurn: (payload: {
    text: string;
    language_code: string;
    session_id?: number;
    interrupted_previous?: boolean;
  }) =>
    request<import("@/types").VoiceTurnResponse>("/voice/turn", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  sendVoiceAudioTurn: (audioBlob: Blob, languageCode: string, sessionId?: number) => {
    const form = new FormData();
    form.append("audio", audioBlob, "utterance.webm");
    form.append("language_code", languageCode);
    if (sessionId) form.append("session_id", String(sessionId));
    return request<import("@/types").VoiceTurnResponse>(
      "/voice/audio-turn",
      { method: "POST", body: form },
      true
    );
  },
};

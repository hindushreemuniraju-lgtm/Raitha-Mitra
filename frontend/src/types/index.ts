export type LanguageCode = "kn-IN" | "hi-IN" | "te-IN" | "en-IN" | "ta-IN" | "mr-IN";

export interface FarmerProfile {
  id: number;
  full_name: string;
  mobile: string;
  email?: string | null;
  state: string;
  district: string;
  taluk?: string;
  village: string;
  location_address?: string | null;
  location_source?: "gps" | "gps_corrected" | "manual" | string;
  latitude?: number | null;
  longitude?: number | null;
  gps_consent: boolean;
  continuous_gps_opt_in?: boolean;
  location_updated_at?: string | null;
  avatar_url?: string | null;
  farm_size_acres: number;
  soil_type?: string | null;
  main_crops: string[];
  preferred_language: LanguageCode | string;
  farmer_category: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ReverseGeocodeResult {
  status: "ok" | "unavailable" | string;
  latitude: number;
  longitude: number;
  village: string;
  taluk: string;
  district: string;
  state: string;
  display_name: string;
  source: string;
  note?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  farmer: FarmerProfile;
}

export interface IntegrationStatusItem {
  name: string;
  configured: boolean;
  status: "configured" | "not_configured";
  note: string;
}

export interface SoilRecord {
  id: number;
  farmer_id: number;
  source_type: "lab_report" | "soil_health_card" | "dataset_estimate";
  dataset_name?: string | null;
  confidence_level: string;
  status: "pending_review" | "verified";
  ph?: number | null;
  nitrogen_kg_ha?: number | null;
  phosphorus_kg_ha?: number | null;
  potassium_kg_ha?: number | null;
  organic_carbon_pct?: number | null;
  ec_ds_m?: number | null;
  sulphur_ppm?: number | null;
  zinc_ppm?: number | null;
  boron_ppm?: number | null;
  iron_ppm?: number | null;
  raw_ocr_text?: string | null;
  original_filename?: string | null;
  file_url?: string | null;
  file_kind?: "image" | "pdf" | string | null;
  file_mime_type?: string | null;
  review_notes?: string | null;
  tested_at?: string | null;
  created_at?: string | null;
}

export interface CropPhotoItem {
  asset_id: string;
  url: string;
  original_filename: string;
}

export interface SoilUploadExtraction {
  record: SoilRecord;
  ocr_status: string;
  ocr_note: string;
  requires_review: boolean;
}

export interface TrackedCrop {
  id: number;
  farmer_id: number;
  crop_name: string;
  variety?: string | null;
  category: string;
  sowing_date: string;
  acreage: number;
  irrigation_type: string;
  current_stage: string;
  completed_tasks: string[];
  photos?: CropPhotoItem[];
  status: string;
  notes?: string | null;
  days_since_sowing: number;
  stage_guidance?: CropStageGuidance | null;
}

export interface CropStageGuidance {
  stage_key: string;
  stage_label: string;
  day_range: string;
  irrigation_advice: string;
  nutrient_advice: string;
  cultivation_tasks: string[];
}

export interface CropRecommendationItem {
  crop_name: string;
  category: "cereal" | "pulse" | "oilseed" | "vegetable" | "fruit" | "spice" | "cash_crop";
  suitability_score: number;
  reasons: string[];
  duration_days: string;
  water_requirement: string;
  nutrient_needs: string;
  estimated_cost_per_acre_inr: string;
  expected_yield_per_acre: string;
  market_value_note: string;
}

export interface CropRecommendationResponse {
  season: string;
  location_summary: string;
  soil_source_used: string;
  missing_soil_fields: string[];
  recommendations: CropRecommendationItem[];
}

export interface WeatherForecastPoint {
  timestamp: string;
  temp_c: number;
  humidity_pct: number;
  rain_mm: number;
  rain_probability_pct?: number;
  wind_kmh: number;
  wind_gust_kmh?: number;
  weather_code?: number;
  condition: string;
}

export interface DailyForecastPoint {
  date: string;
  temp_max_c: number;
  temp_min_c: number;
  rain_sum_mm: number;
  rain_probability_pct: number;
  precipitation_hours: number;
  rain_intensity: "dry" | "light" | "moderate" | "heavy" | "very_heavy" | string;
  wind_max_kmh: number;
  wind_gust_max_kmh?: number;
  weather_code?: number;
  condition: string;
}

export interface ClassifiedAlert {
  alert_type:
    | "official_flood_warning"
    | "heavy_rainfall_warning"
    | "estimated_waterlogging_risk"
    | "general_weather_advisory"
    | string;
  severity: "critical" | "high" | "medium" | "low" | string;
  title_en: string;
  title_kn: string;
  message_en: string;
  message_kn: string;
  source: string;
  is_official: boolean;
}

export interface WeatherWarning {
  severity: "green" | "yellow" | "orange" | "red";
  title: string;
  description: string;
  source: string;
  issued_at?: string | null;
}

export interface WeatherFloodResponse {
  location_label: string;
  latitude?: number | null;
  longitude?: number | null;
  location_source?: string;
  imd_status: "configured" | "not_configured" | "error";
  imd_source_note: string;
  forecast_status: "configured" | "not_configured" | "error";
  forecast_source: string;
  flood_status: "configured" | "not_configured" | "unavailable" | "error";
  flood_source_note: string;
  ksndmc_status?: string;
  ksndmc_source_note?: string;
  updated_at?: string | null;
  freshness_label: string;
  warnings: WeatherWarning[];
  forecast: WeatherForecastPoint[];
  daily_forecast?: DailyForecastPoint[];
  flood_advisories: Array<{
    station: string;
    river: string;
    level_m?: number | null;
    danger_level_m?: number | null;
    status: string;
    source: string;
    updated_at?: string | null;
  }>;
  classified_alerts?: ClassifiedAlert[];
}

export interface DiseaseScan {
  id: number;
  farmer_id: number;
  crop_name?: string | null;
  original_filename?: string | null;
  image_url?: string | null;
  file_mime_type?: string | null;
  adapter_used: string;
  confidence?: number | null;
  status: "diagnosed" | "uncertain" | "not_configured";
  diagnosis_name?: string | null;
  symptoms: string[];
  organic_treatments: string[];
  chemical_treatments: string[];
  precautions: string[];
  raw_summary?: string | null;
  created_at?: string | null;
}

export interface FertilizerItem {
  amendment_name: string;
  amendment_type: "organic" | "chemical" | "micronutrient";
  quantity_kg_total: number;
  quantity_per_acre_kg: number;
  reason: string;
  application_timing: string;
  price_inr?: number | null;
  price_status: string;
  price_source?: string | null;
  price_verified_date?: string | null;
}

export interface FertilizerResponse {
  crop_name: string;
  growth_stage: string;
  farm_size_acres: number;
  soil_basis: string;
  deficiencies_detected: string[];
  missing_soil_parameters: string[];
  organic_plan: FertilizerItem[];
  chemical_plan: FertilizerItem[];
  price_notice: string;
}

export interface YieldPredictionResponse {
  crop_name: string;
  acreage: number;
  yield_min_qtl_total: number;
  yield_expected_qtl_total: number;
  yield_max_qtl_total: number;
  yield_per_acre_range_qtl: string;
  confidence_pct: number;
  confidence_label: string;
  harvest_window_start: string;
  harvest_window_end: string;
  maturity_basis: string[];
  risk_factors: string[];
  google_agri_status: "configured" | "not_configured" | "error";
  google_agri_note: string;
  google_landscape_metadata?: Record<string, unknown> | null;
}

export interface NutritionResponse {
  crop_or_food: string;
  medical_disclaimer: string;
  established_sources: {
    icmr_nin_ifct?: Record<string, unknown> | null;
    fao_infoods_tagnames: string[];
    usda_fdc_status: "configured" | "not_configured" | "error";
    usda_fdc_results: Array<Record<string, unknown>>;
  };
  utilization: {
    preparation: string[];
    storage: string[];
    processing_and_value_addition: string[];
  };
  preliminary_research: {
    pubmed_status: "ok" | "error";
    disclaimer: string;
    articles: Array<{
      pmid: string;
      title: string;
      journal: string;
      pub_date: string;
      url: string;
    }>;
  };
}

export interface MandiPriceRow {
  state: string;
  district: string;
  market: string;
  commodity: string;
  variety: string;
  min_price_inr: number;
  max_price_inr: number;
  modal_price_inr: number;
  arrivals_tonnes?: number | null;
  price_date: string;
  source: string;
}

export interface MandiResponse {
  label: string;
  is_demo_data: boolean;
  source_statuses: Record<string, { status: string; note: string }>;
  updated_at?: string | null;
  records: MandiPriceRow[];
  history_series: Array<{ date: string; modal_price_inr: number; min_price_inr: number; max_price_inr: number }>;
  market_comparison: Array<{ market: string; modal_price_inr: number; arrivals_tonnes?: number | null }>;
}

export interface ProfitCalculateRequest {
  crop_name: string;
  farm_size_acres: number;
  seed_cost: number;
  fertilizer_cost: number;
  pesticide_cost: number;
  labour_cost: number;
  irrigation_cost: number;
  transport_cost: number;
  other_cost: number;
  expected_yield_qtl_per_acre: number;
  expected_price_per_qtl: number;
  save_scenario?: boolean;
}

export interface ProfitScenarioResult {
  id?: number | null;
  crop_name: string;
  farm_size_acres: number;
  total_cost: number;
  expected_revenue: number;
  net_profit: number;
  profit_per_acre: number;
  margin_pct: number;
  breakeven_price_per_qtl: number;
  scenarios: Array<{
    scenario: "Low" | "Expected" | "Optimistic";
    yield_qtl_total: number;
    price_per_qtl: number;
    revenue: number;
    total_cost: number;
    net_profit: number;
    margin_pct: number;
  }>;
  cost_breakdown: Array<{ category: string; amount: number }>;
  disclaimer: string;
  created_at?: string | null;
}

export interface SchemeItem {
  id: string;
  name: string;
  level: "Central" | "State";
  state: string;
  category_tags: string[];
  crop_tags: string[];
  benefits: string;
  eligibility: string[];
  documents_required: string[];
  application_steps: string[];
  official_url: string;
  last_verified: string;
  source: string;
}

export interface SchemesResponse {
  apisetu_status: "configured" | "not_configured" | "error";
  data_gov_status: "configured" | "not_configured" | "error";
  schemes: SchemeItem[];
}

export interface VoiceSession {
  id: number;
  language_code: string;
  room_name?: string | null;
  channel: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface VoiceMessage {
  id: number;
  session_id: number;
  role: "farmer" | "assistant";
  language_code: string;
  content: string;
  interrupted: boolean;
  created_at: string;
}

export interface VoiceTokenResponse {
  livekit_configured: boolean;
  sarvam_configured: boolean;
  status: "ready" | "not_configured";
  livekit_url?: string | null;
  room_name: string;
  token?: string | null;
  language_code: string;
  note: string;
}

export interface VoiceTurnResponse {
  session_id: number;
  language_code: string;
  recognized_text: string;
  reply_text: string;
  audio_base64?: string | null;
  audio_mime?: string | null;
  sarvam_status: "configured" | "not_configured" | "error";
  context_used: Record<string, unknown>;
  missing_data_prompt?: string | null;
  messages: VoiceMessage[];
}

export interface HarvestProfitOptimization {
  market_price_status: "configured" | "not_configured" | string;
  current_modal_price_inr_qtl?: number | null;
  market_name?: string | null;
  price_date?: string | null;
  spoilage_risk_level: "low" | "moderate" | "high" | string;
  recommended_sell_strategy: string;
  transport_timing_advice: string;
  explanation_en: string;
  explanation_kn: string;
  honesty_note: string;
}

export interface HarvestProtectionDecision {
  crop_id?: number | null;
  crop_name: string;
  variety?: string | null;
  sowing_date: string;
  crop_age_days: number;
  current_stage: string;
  expected_maturity_date: string;
  days_remaining_to_maturity: number;
  readiness_status: "immature" | "approaching_maturity" | "harvest_ready" | "overdue" | string;
  action: "harvest_now" | "prepare_harvest" | "wait_for_maturity" | "delay_harvest" | "protect_crop" | string;
  action_label_en: string;
  action_label_kn: string;
  rain_24h_mm: number;
  rain_72h_mm: number;
  max_rain_probability_pct: number;
  max_wind_kmh: number;
  location_label: string;
  headline_en: string;
  headline_kn: string;
  explanation_en: string;
  explanation_kn: string;
  crop_specific_notes: string[];
  precautions_en: string[];
  precautions_kn: string[];
  profit_optimization: HarvestProfitOptimization;
}

export interface HarvestProtectionSummary {
  location_label: string;
  weather_freshness: string;
  decisions: HarvestProtectionDecision[];
}

export interface NotificationItem {
  id: number;
  farmer_id: number;
  crop_id?: number | null;
  category: string;
  alert_type_label: string;
  priority: "critical" | "high" | "medium" | "low" | string;
  dedup_key: string;
  title_en: string;
  title_kn: string;
  message_en: string;
  message_kn: string;
  crop_name?: string | null;
  growth_stage?: string | null;
  recommendation_en?: string | null;
  recommendation_kn?: string | null;
  source_name: string;
  metadata_json: Record<string, unknown>;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface NotificationList {
  unread_count: number;
  total_count: number;
  items: NotificationItem[];
}

export interface DashboardSummary {
  farmer: FarmerProfile;
  weather: WeatherFloodResponse;
  latest_soil?: SoilRecord | null;
  active_crops: TrackedCrop[];
  recent_scans: DiseaseScan[];
  harvest_protection?: HarvestProtectionSummary | null;
  unread_notifications_count?: number;
  recent_notifications?: NotificationItem[];
  mandi_preview: MandiPriceRow[];
  yield_preview?: YieldPredictionResponse | null;
  latest_profit?: ProfitScenarioResult | null;
  suggested_schemes: SchemeItem[];
  integrations_summary: Record<string, IntegrationStatusItem>;
}

"""Verified official Government Schemes filtering service."""

from typing import List, Optional

from config import get_settings
from integrations.schemes_apisetu import ApiSetuMySchemeAdapter
from schemas.schemes import SchemeOut, SchemesListOut


_VERIFIED_OFFICIAL_SCHEMES: List[dict] = [
    {
        "id": "pm-kisan",
        "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "level": "Central",
        "state": "All India",
        "category_tags": ["marginal", "small", "medium", "large"],
        "crop_tags": ["all"],
        "benefits": "Direct income support of ₹6,000 per year in three equal 4-monthly installments of ₹2,000.",
        "eligibility": [
            "Landholding farmer families with cultivable landholding recorded in state/UT land records.",
            "Exclusion criteria apply as published on official pmkisan.gov.in guidelines (e.g., institutional landholders, income tax payers).",
        ],
        "documents_required": ["Aadhaar Card", "Landholding Record (RTC / Khatauni)", "Aadhaar-seeded Bank Account"],
        "application_steps": [
            "Visit pmkisan.gov.in or nearest Common Service Centre (CSC).",
            "Complete e-KYC using Aadhaar OTP or biometric authentication.",
            "Verify land seeding and bank NPCI Aadhaar mapping status.",
        ],
        "official_url": "https://pmkisan.gov.in/",
        "last_verified": "2026-11-01",
        "source": "Department of Agriculture & Farmers Welfare (pmkisan.gov.in)",
    },
    {
        "id": "pmfby",
        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "level": "Central",
        "state": "All India",
        "category_tags": ["marginal", "small", "medium", "large"],
        "crop_tags": ["paddy", "ragi", "maize", "groundnut", "pulses", "horticulture"],
        "benefits": "Crop insurance against yield loss from natural calamities, pests, and diseases; capped farmer premium (2% Kharif, 1.5% Rabi, 5% commercial/horticulture).",
        "eligibility": [
            "Farmers growing notified crops in notified areas (both loanee and non-loanee farmers; voluntary enrollment).",
        ],
        "documents_required": ["Aadhaar Card", "Land Record / Tenancy Agreement", "Sowing Certificate", "Bank Passbook"],
        "application_steps": [
            "Check notified crops and cut-off dates for your district on pmfby.gov.in.",
            "Apply online via PMFBY portal, Crop Insurance App, bank branch, or CSC before season cutoff.",
        ],
        "official_url": "https://pmfby.gov.in/",
        "last_verified": "2026-11-01",
        "source": "Ministry of Agriculture & Farmers Welfare (pmfby.gov.in)",
    },
    {
        "id": "shc",
        "name": "Soil Health Card (SHC) Scheme",
        "level": "Central",
        "state": "All India",
        "category_tags": ["marginal", "small", "medium", "large"],
        "crop_tags": ["all"],
        "benefits": "Free soil testing and crop-wise nutrient & soil amendment recommendations every cycle.",
        "eligibility": ["All farmers across India via State Agriculture Departments and Krishi Vigyan Kendras."],
        "documents_required": ["Aadhaar / Farmer ID", "Plot Survey Number"],
        "application_steps": [
            "Submit soil sample or request collection through local Raitha Samparka Kendra / Agriculture Office.",
            "Download digital Soil Health Card from soilhealth.dac.gov.in and upload it in Raitha Mitra Soil Health tab.",
        ],
        "official_url": "https://soilhealth.dac.gov.in/",
        "last_verified": "2026-11-01",
        "source": "DAC&FW (soilhealth.dac.gov.in)",
    },
    {
        "id": "pmksy-pdmc",
        "name": "Per Drop More Crop (Micro-Irrigation under PMKSY / RKVY)",
        "level": "Central",
        "state": "All India",
        "category_tags": ["marginal", "small", "medium", "large"],
        "crop_tags": ["tomato", "onion", "chilli", "banana", "pomegranate", "papaya", "vegetable", "fruit"],
        "benefits": "Financial assistance / subsidy for drip and sprinkler micro-irrigation systems as per state horticulture/agriculture norms.",
        "eligibility": ["Farmers with owned or leased agricultural land and valid water source; subsidy slabs follow state norms."],
        "documents_required": ["Land RTC / Record", "Aadhaar", "Bank Account", "Water Source Proof"],
        "application_steps": [
            "Apply through your State Agriculture/Horticulture portal (e.g., K-KISAN in Karnataka).",
            "Select empanelled micro-irrigation vendor after work order approval.",
        ],
        "official_url": "https://pmksy.gov.in/",
        "last_verified": "2026-11-01",
        "source": "PMKSY Portal (pmksy.gov.in)",
    },
    {
        "id": "karnataka-raithamitra",
        "name": "Karnataka Dept. of Agriculture Farmer Welfare & Krishi Bhagya / Mechanization",
        "level": "State",
        "state": "Karnataka",
        "category_tags": ["marginal", "small", "medium", "large"],
        "crop_tags": ["ragi", "paddy", "groundnut", "pulses", "horticulture"],
        "benefits": "State subsidies for farm ponds (Krishi Bhagya), seeds, and farm mechanization routed via FRUITS Farmer ID.",
        "eligibility": ["Resident farmers of Karnataka registered on FRUITS (Farmer Registration and Unified Beneficiary Information System)."],
        "documents_required": ["FRUITS FID", "Aadhaar", "RTC Land Record", "Caste Certificate (if applicable)"],
        "application_steps": [
            "Register or verify FRUITS ID at nearest Raitha Samparka Kendra (RSK).",
            "Check active seasonal notifications on raitamitra.karnataka.gov.in.",
        ],
        "official_url": "https://raitamitra.karnataka.gov.in/",
        "last_verified": "2026-11-01",
        "source": "Department of Agriculture, Govt. of Karnataka",
    },
    {
        "id": "myscheme-portal",
        "name": "myScheme National Eligibility Discovery Portal",
        "level": "Central",
        "state": "All India",
        "category_tags": ["marginal", "small", "medium", "large"],
        "crop_tags": ["all"],
        "benefits": "Unified Government of India portal to check state and central agriculture, credit, and rural welfare schemes.",
        "eligibility": ["Open to all Indian citizens based on portal questionnaire filters."],
        "documents_required": ["Varies by selected scheme"],
        "application_steps": [
            "Open myscheme.gov.in, choose Agriculture, Rural & Environment category, and filter by state.",
        ],
        "official_url": "https://www.myscheme.gov.in/",
        "last_verified": "2026-11-01",
        "source": "Digital India / NeGD (myscheme.gov.in)",
    },
]


async def get_filtered_schemes(
    *,
    state: Optional[str] = None,
    category: Optional[str] = None,
    crop: Optional[str] = None,
) -> SchemesListOut:
    settings = get_settings()
    apisetu = ApiSetuMySchemeAdapter()
    apisetu_status = "configured" if apisetu.is_configured else "not_configured"
    data_gov_status = "configured" if settings.DATA_GOV_IN_API_KEY else "not_configured"

    results: List[SchemeOut] = []
    for item in _VERIFIED_OFFICIAL_SCHEMES:
        if state and item["state"] != "All India" and state.strip().lower() not in item["state"].lower():
            continue
        if category and category.strip().lower() not in item["category_tags"]:
            continue
        if crop:
            crop_l = crop.strip().lower()
            if "all" not in item["crop_tags"] and not any(crop_l in t or t in crop_l for t in item["crop_tags"]):
                continue
        results.append(SchemeOut(**item))

    return SchemesListOut(
        apisetu_status=apisetu_status,
        data_gov_status=data_gov_status,
        schemes=results,
    )

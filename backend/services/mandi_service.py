"""Mandi prices aggregation service (data.gov.in AGMARKNET, CEDA, e-NAM honesty)."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from integrations.mandi_agmarknet import AgmarknetDataGovAdapter
from integrations.mandi_ceda import CedaAgmarknetAdapter
from config import get_settings
from schemas.mandi import MandiPriceRowOut, MandiResponseOut


_EXPLICIT_DEMO_ROWS: List[Dict] = [
    {
        "state": "Karnataka",
        "district": "Mandya",
        "market": "Mandya APMC (DEMO DATA)",
        "commodity": "Ragi (Finger Millet)",
        "variety": "Local",
        "min_price_inr": 3250.0,
        "max_price_inr": 3680.0,
        "modal_price_inr": 3490.0,
        "arrivals_tonnes": 42.5,
        "price_date": "DEMO-SAMPLE",
        "source": "DEMO DATA (Not live AGMARKNET)",
    },
    {
        "state": "Karnataka",
        "district": "Kolar",
        "market": "Kolar APMC (DEMO DATA)",
        "commodity": "Tomato",
        "variety": "Hybrid",
        "min_price_inr": 1400.0,
        "max_price_inr": 2100.0,
        "modal_price_inr": 1750.0,
        "arrivals_tonnes": 118.0,
        "price_date": "DEMO-SAMPLE",
        "source": "DEMO DATA (Not live AGMARKNET)",
    },
    {
        "state": "Karnataka",
        "district": "Bengaluru",
        "market": "Yeshwanthpur APMC (DEMO DATA)",
        "commodity": "Onion",
        "variety": "Pune Red",
        "min_price_inr": 1900.0,
        "max_price_inr": 2600.0,
        "modal_price_inr": 2280.0,
        "arrivals_tonnes": 210.0,
        "price_date": "DEMO-SAMPLE",
        "source": "DEMO DATA (Not live AGMARKNET)",
    },
]


async def get_mandi_prices_report(
    *,
    commodity: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    date_str: Optional[str] = None,
    include_demo: bool = False,
) -> MandiResponseOut:
    settings = get_settings()
    agm = AgmarknetDataGovAdapter()
    ceda = CedaAgmarknetAdapter()

    agm_res = await agm.fetch_daily_prices(
        commodity=commodity, state=state, district=district, market=market
    )
    ceda_configured = ceda.is_configured

    statuses = {
        "data_gov_in": {"status": agm_res["status"], "note": agm_res["note"]},
        "ceda_agmarknet": {
            "status": "configured" if ceda_configured else "not_configured",
            "note": "CEDA API ready." if ceda_configured else "CEDA_API_KEY not configured.",
        },
        "enam": {
            "status": "configured" if settings.ENAM_API_URL else "not_configured",
            "note": "e-NAM (enam.gov.in) has no documented public self-service REST API.",
        },
    }

    rows = [MandiPriceRowOut(**r) for r in agm_res["records"]]
    if date_str and rows:
        rows = [r for r in rows if date_str in r.price_date] or rows

    is_demo = False
    if not rows and include_demo:
        is_demo = True
        filtered = [
            r
            for r in _EXPLICIT_DEMO_ROWS
            if (not commodity or commodity.lower() in r["commodity"].lower())
            and (not state or state.lower() in r["state"].lower())
        ] or _EXPLICIT_DEMO_ROWS
        rows = [MandiPriceRowOut(**r) for r in filtered]

    history_series = [
        {
            "date": r.price_date or f"Entry {idx + 1}",
            "modal_price_inr": r.modal_price_inr,
            "min_price_inr": r.min_price_inr,
            "max_price_inr": r.max_price_inr,
        }
        for idx, r in enumerate(rows[:10])
    ]
    market_comparison = [
        {
            "market": r.market,
            "modal_price_inr": r.modal_price_inr,
            "arrivals_tonnes": r.arrivals_tonnes,
        }
        for r in rows[:8]
    ]

    return MandiResponseOut(
        label="DEMO DATA — Latest Available Daily Data (Sample)" if is_demo else "Latest Available Daily Data",
        is_demo_data=is_demo,
        source_statuses=statuses,
        updated_at=datetime.now(timezone.utc).isoformat() if rows else None,
        records=rows,
        history_series=history_series,
        market_comparison=market_comparison,
    )

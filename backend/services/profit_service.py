"""Farm profit calculator and scenario analysis service."""

from typing import List

from sqlalchemy.orm import Session

from models.farmer import Farmer
from models.profit import ProfitScenario
from schemas.profit import ProfitCalculateRequest, ProfitScenarioOut


DISCLAIMER = (
    "Editable farmer estimate only—costs, yields, and mandi prices vary across seasons and are not guaranteed."
)


def _build_scenario_out(
    *,
    scenario_id: int | None,
    crop_name: str,
    acres: float,
    costs: dict[str, float],
    yield_per_acre: float,
    price_per_qtl: float,
    created_at=None,
) -> ProfitScenarioOut:
    total_cost = round(sum(costs.values()), 2)
    expected_qtl_total = round(yield_per_acre * acres, 2)
    expected_revenue = round(expected_qtl_total * price_per_qtl, 2)
    net_profit = round(expected_revenue - total_cost, 2)
    profit_per_acre = round(net_profit / acres, 2)
    margin_pct = round((net_profit / expected_revenue) * 100.0, 2) if expected_revenue > 0 else 0.0
    breakeven_price = round(total_cost / expected_qtl_total, 2) if expected_qtl_total > 0 else 0.0

    scenario_defs = [
        ("Low", 0.80, 0.90),
        ("Expected", 1.00, 1.00),
        ("Optimistic", 1.15, 1.12),
    ]
    scenarios = []
    for name, y_mult, p_mult in scenario_defs:
        q = round(expected_qtl_total * y_mult, 2)
        p = round(price_per_qtl * p_mult, 2)
        rev = round(q * p, 2)
        prof = round(rev - total_cost, 2)
        marg = round((prof / rev) * 100.0, 2) if rev > 0 else 0.0
        scenarios.append(
            {
                "scenario": name,
                "yield_qtl_total": q,
                "price_per_qtl": p,
                "revenue": rev,
                "total_cost": total_cost,
                "net_profit": prof,
                "margin_pct": marg,
            }
        )

    breakdown = [{"category": k, "amount": round(v, 2)} for k, v in costs.items() if v > 0]

    return ProfitScenarioOut(
        id=scenario_id,
        crop_name=crop_name,
        farm_size_acres=acres,
        total_cost=total_cost,
        expected_revenue=expected_revenue,
        net_profit=net_profit,
        profit_per_acre=profit_per_acre,
        margin_pct=margin_pct,
        breakeven_price_per_qtl=breakeven_price,
        scenarios=scenarios,
        cost_breakdown=breakdown,
        disclaimer=DISCLAIMER,
        created_at=created_at,
    )


def calculate_and_optionally_save_profit(
    db: Session, farmer: Farmer, payload: ProfitCalculateRequest
) -> ProfitScenarioOut:
    costs = {
        "Seed": payload.seed_cost,
        "Fertilizer": payload.fertilizer_cost,
        "Pesticide": payload.pesticide_cost,
        "Labour": payload.labour_cost,
        "Irrigation": payload.irrigation_cost,
        "Transport": payload.transport_cost,
        "Other": payload.other_cost,
    }

    result = _build_scenario_out(
        scenario_id=None,
        crop_name=payload.crop_name.strip(),
        acres=payload.farm_size_acres,
        costs=costs,
        yield_per_acre=payload.expected_yield_qtl_per_acre,
        price_per_qtl=payload.expected_price_per_qtl,
    )

    if payload.save_scenario:
        row = ProfitScenario(
            farmer_id=farmer.id,
            crop_name=result.crop_name,
            farm_size_acres=result.farm_size_acres,
            seed_cost=payload.seed_cost,
            fertilizer_cost=payload.fertilizer_cost,
            pesticide_cost=payload.pesticide_cost,
            labour_cost=payload.labour_cost,
            irrigation_cost=payload.irrigation_cost,
            transport_cost=payload.transport_cost,
            other_cost=payload.other_cost,
            expected_yield_qtl_per_acre=payload.expected_yield_qtl_per_acre,
            expected_price_per_qtl=payload.expected_price_per_qtl,
            total_cost=result.total_cost,
            expected_revenue=result.expected_revenue,
            net_profit=result.net_profit,
            margin_pct=result.margin_pct,
            assumptions_json={"scenarios": result.scenarios},
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        result.id = row.id
        result.created_at = row.created_at

    return result


def list_farmer_profit_scenarios(db: Session, farmer_id: int) -> List[ProfitScenarioOut]:
    rows = (
        db.query(ProfitScenario)
        .filter(ProfitScenario.farmer_id == farmer_id)
        .order_by(ProfitScenario.created_at.desc())
        .all()
    )
    out: List[ProfitScenarioOut] = []
    for r in rows:
        costs = {
            "Seed": r.seed_cost,
            "Fertilizer": r.fertilizer_cost,
            "Pesticide": r.pesticide_cost,
            "Labour": r.labour_cost,
            "Irrigation": r.irrigation_cost,
            "Transport": r.transport_cost,
            "Other": r.other_cost,
        }
        out.append(
            _build_scenario_out(
                scenario_id=r.id,
                crop_name=r.crop_name,
                acres=r.farm_size_acres,
                costs=costs,
                yield_per_acre=r.expected_yield_qtl_per_acre,
                price_per_qtl=r.expected_price_per_qtl,
                created_at=r.created_at,
            )
        )
    return out

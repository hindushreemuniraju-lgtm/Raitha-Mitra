"""Downloadable SoilGrids / ISRO Bhuvan local dataset reader (never paused SoilGrids REST API)."""

import csv
import math
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_settings


class SoilDatasetAdapter:
    """
    Reads local downloadable SoilGrids (GeoTIFF/CSV extract) or ISRO Bhuvan soil datasets
    stored under SOIL_DATASET_PATH. Never calls the paused rest.isric.org REST API.
    """

    def __init__(self):
        self.settings = get_settings()

    def _find_csv_datasets(self) -> list[Path]:
        base = Path(self.settings.SOIL_DATASET_PATH)
        if not base.exists():
            return []
        return sorted(base.glob("*.csv"))

    def lookup_by_coordinates(
        self, latitude: float, longitude: float, dataset_preference: str = "auto"
    ) -> Dict[str, Any]:
        csv_files = self._find_csv_datasets()
        if not csv_files:
            return {
                "configured": False,
                "dataset_name": None,
                "confidence_level": "unavailable",
                "note": (
                    "No downloaded Bhuvan or SoilGrids dataset extracts found in SOIL_DATASET_PATH. "
                    "Download GeoTIFF/CSV tiles from files.isric.org/soilgrids/latest/data/ or "
                    "bhuvan.nrsc.gov.in, or upload a lab Soil Health Card."
                ),
                "values": {},
            }

        best_row: Optional[Dict[str, str]] = None
        best_dist = float("inf")
        best_file = csv_files[0].name

        for csv_path in csv_files:
            if dataset_preference != "auto" and dataset_preference.lower() not in csv_path.name.lower():
                continue
            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    try:
                        rlat = float(row["latitude"])
                        rlon = float(row["longitude"])
                    except (KeyError, ValueError, TypeError):
                        continue
                    dist = math.hypot(latitude - rlat, longitude - rlon)
                    if dist < best_dist:
                        best_dist = dist
                        best_row = row
                        best_file = csv_path.name

        if best_row is None or best_dist > 1.5:
            return {
                "configured": True,
                "dataset_name": best_file,
                "confidence_level": "unavailable",
                "note": "Coordinates are outside the coverage of downloaded local soil dataset extracts.",
                "values": {},
            }

        confidence = "medium" if best_dist <= 0.25 else "low"

        def _opt_float(key: str) -> Optional[float]:
            val = best_row.get(key)
            if val is None or val == "":
                return None
            try:
                return round(float(val), 2)
            except ValueError:
                return None

        return {
            "configured": True,
            "dataset_name": f"Local Extract ({best_file})",
            "confidence_level": confidence,
            "note": f"ESTIMATED from downloaded dataset '{best_file}' (nearest grid point ~{best_dist:.3f}° away). Lab values override estimates.",
            "values": {
                "ph": _opt_float("ph"),
                "nitrogen_kg_ha": _opt_float("nitrogen_kg_ha"),
                "phosphorus_kg_ha": _opt_float("phosphorus_kg_ha"),
                "potassium_kg_ha": _opt_float("potassium_kg_ha"),
                "organic_carbon_pct": _opt_float("organic_carbon_pct"),
                "ec_ds_m": _opt_float("ec_ds_m"),
            },
        }

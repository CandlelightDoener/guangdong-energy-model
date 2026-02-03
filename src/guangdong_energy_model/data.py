"""
Energy data for Guangdong Province, China.

Capacity data is loaded from the Global Energy Monitor (GEM) Global Integrated
Power Tracker when available.  Demand/load data comes from PyPSA-China-PIK.
Falls back to estimated values when data files are not present.

GEM data: download from https://globalenergymonitor.org/projects/global-integrated-power-tracker/download-data/
PyPSA-China-PIK: git submodule update --init --recursive
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# --- PyPSA-China-PIK demand data -------------------------------------------

_USE_REAL_DATA = False
_REAL_DATA = {}

try:
    from . import data_loader
    _REAL_DATA = data_loader.get_guangdong_summary()
    _USE_REAL_DATA = True
    logger.info("Using real data from PyPSA-China-PIK")
except Exception as e:
    logger.warning(f"PyPSA-China-PIK data not available: {e}")
    logger.warning("Using placeholder data. Run: git submodule update --init --recursive")

# --- GEM capacity data -----------------------------------------------------

_GEM_CAPACITIES: dict[str, float] | None = None  # populated by load_gem_data()


def load_gem_data(gem_path: Path | None = None) -> None:
    """Load GEM capacity data.  Called from main() or manually.

    Args:
        gem_path: Explicit path to GEM Excel file, or None to auto-detect.
    """
    global _GEM_CAPACITIES
    from . import gem_loader

    caps = gem_loader.load_gem_capacities(gem_path)
    if caps:
        _GEM_CAPACITIES = caps
        _apply_gem_capacities()
        logger.info("Installed capacities updated from GEM data")
    else:
        logger.info("GEM data not available — using fallback estimates")


def _apply_gem_capacities() -> None:
    """Overwrite INSTALLED_CAPACITY_GW with GEM values where available."""
    if _GEM_CAPACITIES is None:
        return

    gem = _GEM_CAPACITIES

    # Map GEM carriers to the keys used in INSTALLED_CAPACITY_GW.
    # GEM distinguishes CCGT/OCGT and onwind/offwind; we aggregate to the
    # broader categories used by the rest of the model.
    INSTALLED_CAPACITY_GW["coal"] = round(gem.get("coal", 0.0), 1)
    INSTALLED_CAPACITY_GW["CCGT"] = round(gem.get("CCGT", 0.0), 1)
    INSTALLED_CAPACITY_GW["OCGT"] = round(gem.get("OCGT", 0.0), 1)
    INSTALLED_CAPACITY_GW["nuclear"] = round(gem.get("nuclear", 0.0), 1)
    INSTALLED_CAPACITY_GW["hydro"] = round(gem.get("hydro", 0.0), 1)
    INSTALLED_CAPACITY_GW["PHS"] = round(gem.get("PHS", 0.0), 1)
    INSTALLED_CAPACITY_GW["solar"] = round(gem.get("solar", 0.0), 1)
    INSTALLED_CAPACITY_GW["onwind"] = round(gem.get("onwind", 0.0), 1)
    INSTALLED_CAPACITY_GW["offwind"] = round(gem.get("offwind", 0.0), 1)
    INSTALLED_CAPACITY_GW["biomass"] = round(gem.get("biomass", 0.0), 1)

    # Remove the old aggregated keys that are now split
    INSTALLED_CAPACITY_GW.pop("gas", None)
    INSTALLED_CAPACITY_GW.pop("wind", None)


def is_using_real_data() -> bool:
    """Check if real data from PyPSA-China-PIK is being used."""
    return _USE_REAL_DATA


def is_using_gem_data() -> bool:
    """Check if GEM capacity data has been loaded."""
    return _GEM_CAPACITIES is not None


def get_gem_capacities() -> dict[str, float] | None:
    """Return the raw GEM capacity dict (GW), or None."""
    return _GEM_CAPACITIES


def get_real_data_summary() -> dict:
    """Get summary of loaded real data."""
    return _REAL_DATA


def _safe_get(key: str, default: float) -> float:
    """Safely get numeric value from real data, with fallback."""
    if not _USE_REAL_DATA:
        return default
    value = _REAL_DATA.get(key)
    if value is None or isinstance(value, str):
        return default
    return float(value)


# --- Installed capacity (GW) -----------------------------------------------
# Defaults are estimates; overwritten by _apply_gem_capacities() when GEM is loaded.

_nuclear_gw = _safe_get("nuclear_capacity_mw", 16000) / 1000

INSTALLED_CAPACITY_GW: dict[str, float] = {
    "coal": 65.0,        # Thermal coal plants
    "gas": 25.0,         # Natural gas (CCGT + OCGT combined)
    "nuclear": round(_nuclear_gw, 1),
    "hydro": 12.0,       # Conventional hydro
    "solar": 35.0,       # Rapid growth in recent years
    "wind": 12.0,        # Offshore and onshore combined
    "biomass": 3.0,      # Waste-to-energy, agricultural
}

# Capacity factors (annual average)
CAPACITY_FACTORS = {
    "coal": 0.55,
    "gas": 0.35,
    "CCGT": 0.40,
    "OCGT": 0.15,
    "nuclear": 0.85,
    "hydro": 0.35,
    "PHS": 0.20,
    "solar": 0.14,
    "wind": 0.22,
    "onwind": 0.20,
    "offwind": 0.28,
    "biomass": 0.60,
}

# Marginal costs in CNY/MWh
MARGINAL_COSTS_CNY = {
    "coal": 350,
    "gas": 550,
    "CCGT": 500,
    "OCGT": 650,
    "nuclear": 50,
    "hydro": 20,
    "PHS": 15,
    "solar": 0,
    "wind": 0,
    "onwind": 0,
    "offwind": 0,
    "biomass": 200,
}

# Capital costs in CNY/kW (for expansion planning)
CAPITAL_COSTS_CNY_KW = {
    "coal": 4500,
    "gas": 3500,
    "nuclear": 18000,
    "hydro": 8000,
    "solar": 3000,
    "wind_onshore": 5500,
    "wind_offshore": 12000,
    "biomass": 8000,
    "battery_4h": 1500,
}

# CO2 emissions in tons/MWh
CO2_EMISSIONS_T_MWH = {
    "coal": 0.85,
    "gas": 0.40,
    "CCGT": 0.37,
    "OCGT": 0.50,
    "nuclear": 0.0,
    "hydro": 0.0,
    "PHS": 0.0,
    "solar": 0.0,
    "wind": 0.0,
    "onwind": 0.0,
    "offwind": 0.0,
    "biomass": 0.0,  # Considered carbon-neutral
}

# Primary energy consumption by sector (PJ/year, estimated 2023)
PRIMARY_ENERGY_PJ = {
    "coal": 4500,       # Including for power, industry, heating
    "oil": 2800,        # Transport, petrochemicals
    "natural_gas": 1200,
    "nuclear": 450,
    "hydro": 150,
    "wind": 100,
    "solar": 180,
    "biomass": 200,
}

# Electricity consumption by sector (TWh/year)
# Total from real data: 912 TWh (2025), distributed by typical shares
_total_demand_twh = _safe_get("annual_demand_2025_twh", 800)

ELECTRICITY_DEMAND_TWH = {
    "industrial": round(_total_demand_twh * 0.65),   # 65%
    "commercial": round(_total_demand_twh * 0.175),  # 17.5%
    "residential": round(_total_demand_twh * 0.125), # 12.5%
    "transport": round(_total_demand_twh * 0.03),    # 3%
    "agriculture": round(_total_demand_twh * 0.02),  # 2%
}

# Peak load in GW (from real hourly data if available)
_peak_mw = _safe_get("peak_demand_mw", 145000)
PEAK_LOAD_GW = round(_peak_mw / 1000, 1)

# Typical load profile factors (hourly, normalized)
# Simplified 24-hour profile for a typical summer day
LOAD_PROFILE_SUMMER = [
    0.70, 0.65, 0.62, 0.60, 0.60, 0.62,  # 00:00 - 05:00
    0.68, 0.78, 0.88, 0.95, 0.98, 1.00,  # 06:00 - 11:00
    0.98, 0.95, 0.96, 0.98, 1.00, 0.98,  # 12:00 - 17:00
    0.95, 0.92, 0.88, 0.85, 0.80, 0.75,  # 18:00 - 23:00
]

# Solar availability profile (normalized, typical summer day)
SOLAR_PROFILE = [
    0.00, 0.00, 0.00, 0.00, 0.00, 0.05,  # 00:00 - 05:00
    0.20, 0.45, 0.70, 0.88, 0.95, 1.00,  # 06:00 - 11:00
    0.98, 0.92, 0.82, 0.65, 0.40, 0.15,  # 12:00 - 17:00
    0.02, 0.00, 0.00, 0.00, 0.00, 0.00,  # 18:00 - 23:00
]

# Wind availability profile (normalized, typical day)
WIND_PROFILE = [
    0.35, 0.38, 0.40, 0.42, 0.45, 0.48,  # 00:00 - 05:00
    0.45, 0.40, 0.32, 0.28, 0.25, 0.22,  # 06:00 - 11:00
    0.20, 0.22, 0.25, 0.30, 0.35, 0.42,  # 12:00 - 17:00
    0.48, 0.50, 0.48, 0.45, 0.42, 0.38,  # 18:00 - 23:00
]

# Regional breakdown within Guangdong (for multi-node models)
REGIONS = {
    "pearl_river_delta": {
        "load_share": 0.70,
        "description": "Guangzhou, Shenzhen, Dongguan, Foshan, etc."
    },
    "east_guangdong": {
        "load_share": 0.12,
        "description": "Shantou, Chaozhou, Jieyang, Meizhou"
    },
    "west_guangdong": {
        "load_share": 0.10,
        "description": "Zhanjiang, Maoming, Yangjiang"
    },
    "north_guangdong": {
        "load_share": 0.08,
        "description": "Shaoguan, Qingyuan, Yunfu"
    },
}

# Inter-provincial power transfers (GW capacity)
IMPORT_CAPACITY_GW = {
    "west_east_power": 50.0,  # From Yunnan, Guizhou (hydro)
    "hong_kong_link": 4.0,
}


def get_hourly_demand_profile(n_hours: int = 8760):
    """
    Get hourly demand profile in MW.

    Uses real data from PyPSA-China-PIK if available,
    otherwise generates synthetic profile from LOAD_PROFILE_SUMMER.

    Args:
        n_hours: Number of hours to return (default: full year)

    Returns:
        numpy array of hourly demand in MW
    """
    import numpy as np

    if _USE_REAL_DATA:
        try:
            hourly = data_loader.load_hourly_demand()
            return hourly.values[:n_hours]
        except Exception as e:
            logger.warning(f"Failed to load hourly data: {e}")

    # Fallback: generate from simplified profile
    profile = np.array(LOAD_PROFILE_SUMMER)
    peak_mw = PEAK_LOAD_GW * 1000
    full_year = np.tile(profile, 365)[:n_hours]
    return full_year * peak_mw

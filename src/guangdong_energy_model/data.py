"""
Energy data for Guangdong Province, China.

Real data is loaded from PyPSA-China-PIK when available.
Fallback to estimated values if submodule not initialized.

To get real data:
    git submodule update --init --recursive

To update data:
    git submodule update --remote
"""

import logging

logger = logging.getLogger(__name__)

# Try to load real data from PyPSA-China-PIK
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


def is_using_real_data() -> bool:
    """Check if real data from PyPSA-China-PIK is being used."""
    return _USE_REAL_DATA


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


# Installed capacity in GW
# Nuclear capacity from real data if available (16.136 GW from PyPSA-China-PIK)
_nuclear_gw = _safe_get("nuclear_capacity_mw", 16000) / 1000

INSTALLED_CAPACITY_GW = {
    "coal": 65.0,        # Thermal coal plants
    "gas": 25.0,         # Natural gas (CCGT, peaker)
    "nuclear": round(_nuclear_gw, 1),
    "hydro": 12.0,       # Including pumped hydro
    "solar": 35.0,       # Rapid growth in recent years
    "wind": 12.0,        # Offshore and onshore
    "biomass": 3.0,      # Waste-to-energy, agricultural
}

# Capacity factors (annual average)
CAPACITY_FACTORS = {
    "coal": 0.55,
    "gas": 0.35,
    "nuclear": 0.85,
    "hydro": 0.35,
    "solar": 0.14,
    "wind": 0.22,
    "biomass": 0.60,
}

# Marginal costs in CNY/MWh
MARGINAL_COSTS_CNY = {
    "coal": 350,
    "gas": 550,
    "nuclear": 50,
    "hydro": 20,
    "solar": 0,
    "wind": 0,
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
    "nuclear": 0.0,
    "hydro": 0.0,
    "solar": 0.0,
    "wind": 0.0,
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

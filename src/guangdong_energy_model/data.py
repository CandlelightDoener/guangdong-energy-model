"""
Energy data for Guangdong Province, China.

Data sources (estimated/placeholder values based on public statistics):
- China Statistical Yearbook
- Guangdong Provincial Statistics
- National Energy Administration reports

Note: These are approximate values for demonstration purposes.
Actual modeling should use verified data from official sources.
"""

# Guangdong Province Key Statistics (2023 estimates)
# Population: ~127 million
# GDP: ~13.5 trillion CNY
# Total electricity consumption: ~800 TWh/year

# Installed capacity in GW (estimated 2023)
INSTALLED_CAPACITY_GW = {
    "coal": 65.0,        # Thermal coal plants
    "gas": 25.0,         # Natural gas (CCGT, peaker)
    "nuclear": 16.0,     # Daya Bay, Yangjiang, Taishan, etc.
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

# Electricity consumption by sector (TWh/year, estimated 2023)
ELECTRICITY_DEMAND_TWH = {
    "industrial": 520,
    "commercial": 140,
    "residential": 100,
    "transport": 25,
    "agriculture": 15,
}

# Peak load in GW
PEAK_LOAD_GW = 145.0

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

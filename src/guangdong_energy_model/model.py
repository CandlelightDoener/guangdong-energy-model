"""
PyPSA Energy System Model for Guangdong Province, China.

This module creates a multi-sector energy system model including:
- Electricity generation (coal, gas, nuclear, hydro, solar, wind)
- Energy storage (battery, pumped hydro)
- Sectoral electricity demand
- Primary energy supply chains
"""

import pypsa
import pandas as pd
import numpy as np
from pathlib import Path

from . import data


def create_network(
    snapshots: int = 24,
    multi_region: bool = False,
    include_storage: bool = True,
) -> pypsa.Network:
    """
    Create a PyPSA network for Guangdong Province.

    Args:
        snapshots: Number of time steps (default 24 for hourly day)
        multi_region: If True, create multi-node regional model
        include_storage: If True, include battery and pumped hydro storage

    Returns:
        Configured PyPSA Network
    """
    network = pypsa.Network()
    network.name = "Guangdong Province Energy System"

    # Set snapshots (hourly for one day as example)
    network.set_snapshots(pd.date_range("2023-07-15", periods=snapshots, freq="h"))

    if multi_region:
        _add_regional_buses(network)
        _add_transmission_lines(network)
    else:
        _add_single_bus(network)

    _add_generators(network, multi_region)
    _add_loads(network, multi_region)

    if include_storage:
        _add_storage(network, multi_region)

    _add_imports(network, multi_region)

    return network


def _add_single_bus(network: pypsa.Network) -> None:
    """Add a single electricity bus for simplified model."""
    network.add("Bus", "guangdong_elec", carrier="AC", v_nom=500)
    network.add("Bus", "guangdong_heat", carrier="heat")
    network.add("Bus", "guangdong_gas", carrier="gas")


def _add_regional_buses(network: pypsa.Network) -> None:
    """Add regional buses for multi-node model."""
    for region in data.REGIONS:
        network.add("Bus", f"{region}_elec", carrier="AC", v_nom=500)
        network.add("Bus", f"{region}_heat", carrier="heat")


def _add_transmission_lines(network: pypsa.Network) -> None:
    """Add transmission lines between regions."""
    # Pearl River Delta is the hub
    connections = [
        ("pearl_river_delta_elec", "east_guangdong_elec", 15.0),
        ("pearl_river_delta_elec", "west_guangdong_elec", 12.0),
        ("pearl_river_delta_elec", "north_guangdong_elec", 10.0),
    ]
    for bus0, bus1, capacity in connections:
        network.add(
            "Line",
            f"{bus0}-{bus1}",
            bus0=bus0,
            bus1=bus1,
            s_nom=capacity * 1000,  # Convert GW to MW
            x=0.01,
            r=0.001,
        )


def _add_generators(network: pypsa.Network, multi_region: bool) -> None:
    """Add all generator types to the network."""
    if multi_region:
        # Distribute capacity across regions based on typical locations
        _add_regional_generators(network)
    else:
        bus = "guangdong_elec"
        for gen_type, capacity_gw in data.INSTALLED_CAPACITY_GW.items():
            p_max_pu = _get_availability_profile(
                gen_type, len(network.snapshots)
            )
            network.add(
                "Generator",
                f"{gen_type}_plant",
                bus=bus,
                p_nom=capacity_gw * 1000,  # GW to MW
                marginal_cost=data.MARGINAL_COSTS_CNY[gen_type],
                carrier=gen_type,
                p_max_pu=p_max_pu,
            )


def _add_regional_generators(network: pypsa.Network) -> None:
    """Add generators distributed across regions."""
    # Regional distribution of generation capacity
    regional_shares = {
        "pearl_river_delta": {
            "coal": 0.40, "gas": 0.70, "nuclear": 0.60,
            "solar": 0.50, "wind": 0.30, "hydro": 0.10, "biomass": 0.50,
        },
        "east_guangdong": {
            "coal": 0.20, "gas": 0.10, "nuclear": 0.20,
            "solar": 0.15, "wind": 0.25, "hydro": 0.10, "biomass": 0.15,
        },
        "west_guangdong": {
            "coal": 0.25, "gas": 0.15, "nuclear": 0.20,
            "solar": 0.20, "wind": 0.35, "hydro": 0.20, "biomass": 0.20,
        },
        "north_guangdong": {
            "coal": 0.15, "gas": 0.05, "nuclear": 0.00,
            "solar": 0.15, "wind": 0.10, "hydro": 0.60, "biomass": 0.15,
        },
    }

    n_snapshots = len(network.snapshots)

    for region, shares in regional_shares.items():
        bus = f"{region}_elec"
        for gen_type, share in shares.items():
            if share > 0:
                capacity = data.INSTALLED_CAPACITY_GW[gen_type] * share * 1000
                p_max_pu = _get_availability_profile(gen_type, n_snapshots)
                network.add(
                    "Generator",
                    f"{region}_{gen_type}",
                    bus=bus,
                    p_nom=capacity,
                    marginal_cost=data.MARGINAL_COSTS_CNY[gen_type],
                    carrier=gen_type,
                    p_max_pu=p_max_pu,
                )


def _get_availability_profile(gen_type: str, n_snapshots: int) -> np.ndarray:
    """Get hourly availability profile for generator type."""
    if gen_type == "solar":
        profile = np.array(data.SOLAR_PROFILE)
    elif gen_type == "wind":
        profile = np.array(data.WIND_PROFILE)
    else:
        # Dispatchable generators - full availability
        return 1.0

    # Tile or truncate to match snapshots
    if n_snapshots <= 24:
        return profile[:n_snapshots]
    else:
        return np.tile(profile, (n_snapshots // 24) + 1)[:n_snapshots]


def _add_loads(network: pypsa.Network, multi_region: bool) -> None:
    """Add electricity loads by sector."""
    total_annual_twh = sum(data.ELECTRICITY_DEMAND_TWH.values())
    # Convert annual TWh to hourly MW (assuming 8760 hours)
    avg_hourly_mw = total_annual_twh * 1e6 / 8760

    # Create load profile
    load_profile = np.array(data.LOAD_PROFILE_SUMMER)

    if multi_region:
        for region, info in data.REGIONS.items():
            bus = f"{region}_elec"
            regional_load = avg_hourly_mw * info["load_share"]
            n_snapshots = len(network.snapshots)
            p_set = regional_load * load_profile[:n_snapshots]

            network.add(
                "Load",
                f"{region}_demand",
                bus=bus,
                p_set=p_set,
            )
    else:
        n_snapshots = len(network.snapshots)
        p_set = avg_hourly_mw * load_profile[:n_snapshots]

        # Add sectoral loads
        for sector, twh in data.ELECTRICITY_DEMAND_TWH.items():
            sector_share = twh / total_annual_twh
            network.add(
                "Load",
                f"{sector}_load",
                bus="guangdong_elec",
                p_set=p_set * sector_share,
            )


def _add_storage(network: pypsa.Network, multi_region: bool) -> None:
    """Add energy storage units."""
    bus = "pearl_river_delta_elec" if multi_region else "guangdong_elec"

    # Battery storage (4-hour duration assumed)
    network.add(
        "StorageUnit",
        "battery_storage",
        bus=bus,
        p_nom=5000,  # 5 GW
        max_hours=4,
        efficiency_store=0.92,
        efficiency_dispatch=0.92,
        marginal_cost=5,
        carrier="battery",
    )

    # Pumped hydro storage
    network.add(
        "StorageUnit",
        "pumped_hydro",
        bus=bus,
        p_nom=8000,  # 8 GW
        max_hours=8,
        efficiency_store=0.85,
        efficiency_dispatch=0.87,
        marginal_cost=2,
        carrier="pumped_hydro",
    )


def _add_imports(network: pypsa.Network, multi_region: bool) -> None:
    """Add inter-provincial power imports (West-East Power Transfer)."""
    bus = "pearl_river_delta_elec" if multi_region else "guangdong_elec"

    # West-East Power Transfer (mainly hydro from Yunnan/Guizhou)
    network.add(
        "Generator",
        "west_east_import",
        bus=bus,
        p_nom=data.IMPORT_CAPACITY_GW["west_east_power"] * 1000,
        marginal_cost=280,  # Lower cost hydro imports
        carrier="import_hydro",
        p_max_pu=0.8,  # High availability from contracted power
    )


def solve_network(
    network: pypsa.Network,
    solver_name: str = "highs",
) -> pypsa.Network:
    """
    Solve the network optimization problem.

    Args:
        network: PyPSA network to solve
        solver_name: Solver to use (highs, glpk, gurobi, cplex)

    Returns:
        Solved network
    """
    network.optimize(solver_name=solver_name)
    return network


def get_generation_summary(network: pypsa.Network) -> pd.DataFrame:
    """Get summary of generation by carrier."""
    if network.generators_t.p.empty:
        return pd.DataFrame()

    gen_by_carrier = network.generators_t.p.T.groupby(
        network.generators.carrier
    ).sum().T

    summary = pd.DataFrame({
        "Total Generation (MWh)": gen_by_carrier.sum(),
        "Peak Generation (MW)": gen_by_carrier.max(),
        "Capacity Factor": gen_by_carrier.sum() / (
            network.generators.groupby("carrier").p_nom.sum() * len(network.snapshots)
        ),
    })
    return summary.round(2)


def get_emissions_summary(network: pypsa.Network) -> dict:
    """Calculate total CO2 emissions from generation."""
    if network.generators_t.p.empty:
        return {}

    total_emissions = 0
    for gen in network.generators.index:
        carrier = network.generators.loc[gen, "carrier"]
        if carrier in data.CO2_EMISSIONS_T_MWH:
            generation_mwh = network.generators_t.p[gen].sum()
            emissions = generation_mwh * data.CO2_EMISSIONS_T_MWH[carrier]
            total_emissions += emissions

    return {
        "total_co2_tonnes": round(total_emissions, 0),
        "co2_intensity_kg_mwh": round(
            total_emissions * 1000 / network.loads_t.p_set.sum().sum(), 1
        ),
    }


def get_cost_summary(network: pypsa.Network) -> dict:
    """Get cost summary of the solved network."""
    if not hasattr(network, "objective") or network.objective is None:
        return {}

    return {
        "total_cost_cny": round(network.objective, 0),
        "avg_cost_cny_mwh": round(
            network.objective / network.loads_t.p_set.sum().sum(), 2
        ),
    }

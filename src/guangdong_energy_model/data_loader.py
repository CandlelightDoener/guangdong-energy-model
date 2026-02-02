"""
Data loader for PyPSA-China-PIK real data.

Loads provincial energy data from the PyPSA-China-PIK submodule.
Update with: git submodule update --remote
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os

# Path to PyPSA-China-PIK data
# Try multiple possible locations
def _find_data_root() -> Path:
    """Find the PyPSA-China-PIK data directory."""
    # Option 1: Relative to this file (development mode)
    dev_path = Path(__file__).parent.parent.parent.parent / "external" / "pypsa-china" / "resources" / "data"
    if dev_path.exists():
        return dev_path

    # Option 2: From environment variable
    env_path = os.environ.get("PYPSA_CHINA_DATA")
    if env_path and Path(env_path).exists():
        return Path(env_path)

    # Option 3: Relative to current working directory
    cwd_path = Path.cwd() / "external" / "pypsa-china" / "resources" / "data"
    if cwd_path.exists():
        return cwd_path

    # Return dev path (will raise error later if not found)
    return dev_path


DATA_ROOT = _find_data_root()

PROVINCE = "Guangdong"
PROVINCE_CODE = "GD"


def get_data_path() -> Path:
    """Get path to PyPSA-China-PIK data directory."""
    if not DATA_ROOT.exists():
        raise FileNotFoundError(
            f"PyPSA-China-PIK data not found at {DATA_ROOT}. "
            "Run: git submodule update --init --recursive"
        )
    return DATA_ROOT


def load_nuclear_capacity() -> float:
    """Load nuclear capacity for Guangdong in MW."""
    path = get_data_path() / "p_nom" / "nuclear_p_nom.csv"
    df = pd.read_csv(path)
    row = df[df["Province"] == PROVINCE]
    if row.empty:
        return 0.0
    return float(row["nuclear_capacity"].values[0])


def load_annual_demand(year: int = 2025) -> float:
    """Load annual electricity demand for Guangdong in MWh."""
    path = get_data_path() / "load" / "Provincial_Load_2020_2060_MWh.csv"
    df = pd.read_csv(path, index_col=0)
    if PROVINCE not in df.index:
        raise ValueError(f"Province {PROVINCE} not found in load data")
    return float(df.loc[PROVINCE, str(year)])


def load_hourly_demand() -> pd.Series:
    """
    Load hourly electricity demand profile for Guangdong.

    Returns:
        pd.Series with 8760 hourly values in MW
    """
    path = get_data_path() / "load" / "Hourly_demand_of_31_province_China_modified_V2.1.csv"
    df = pd.read_csv(path)
    if PROVINCE_CODE not in df.columns:
        raise ValueError(f"Province code {PROVINCE_CODE} not found in hourly data")
    return df[PROVINCE_CODE]


def load_hydro_capacity() -> dict:
    """Load hydro capacity data for Guangdong."""
    try:
        import h5py
        path = get_data_path() / "p_nom" / "hydro_p_nom.h5"
        with h5py.File(path, "r") as f:
            # Structure depends on HDF5 file format
            # Return empty dict if structure unknown
            return {}
    except ImportError:
        return {}


def load_heating_demand() -> pd.DataFrame | None:
    """Load heating demand data if available."""
    heating_path = get_data_path() / "heating"
    if not heating_path.exists():
        return None
    # Load heating data files
    # Structure depends on available files
    return None


def load_cost_data(year: int = 2025) -> pd.DataFrame:
    """Load technology cost data for a given year."""
    path = get_data_path() / "costs" / "default" / f"costs_{year}.csv"
    if not path.exists():
        # Fall back to nearest available year
        available = list((get_data_path() / "costs" / "default").glob("costs_*.csv"))
        if not available:
            raise FileNotFoundError("No cost data found")
        path = available[0]
    return pd.read_csv(path)


def get_guangdong_summary() -> dict:
    """Get summary of all available Guangdong data."""
    summary = {
        "province": PROVINCE,
        "province_code": PROVINCE_CODE,
    }

    try:
        summary["nuclear_capacity_mw"] = load_nuclear_capacity()
    except Exception as e:
        summary["nuclear_capacity_mw"] = f"Error: {e}"

    try:
        summary["annual_demand_2025_mwh"] = load_annual_demand(2025)
        summary["annual_demand_2025_twh"] = load_annual_demand(2025) / 1e6
    except Exception as e:
        summary["annual_demand_2025_twh"] = f"Error: {e}"

    try:
        hourly = load_hourly_demand()
        summary["peak_demand_mw"] = float(hourly.max())
        summary["min_demand_mw"] = float(hourly.min())
        summary["avg_demand_mw"] = float(hourly.mean())
    except Exception as e:
        summary["hourly_demand"] = f"Error: {e}"

    return summary


if __name__ == "__main__":
    # Test data loading
    print("Guangdong Energy Data Summary")
    print("=" * 40)
    summary = get_guangdong_summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"{key}: {value:,.2f}")
        else:
            print(f"{key}: {value}")

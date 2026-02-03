"""
GEM (Global Energy Monitor) data loader for power plant capacities.

Loads real installed capacity data from the Global Integrated Power Tracker
(GIPT) Excel file published by Global Energy Monitor.

Data source: https://globalenergymonitor.org/projects/global-integrated-power-tracker/
License: CC BY 4.0
"""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PROVINCE = "Guangdong"

# Default search paths for the GEM Excel file
DEFAULT_PATHS = [
    Path("data"),
    Path(__file__).parent.parent.parent.parent / "data",
]

# Map GEM Type + Technology to PyPSA carrier names
_TECH_MAP = {
    # (Type, Technology) -> carrier
    # Coal
    ("coal", None): "coal",
    # Oil/Gas
    ("oil/gas", "combined cycle"): "CCGT",
    ("oil/gas", "gas turbine"): "OCGT",
    ("oil/gas", "steam turbine"): "OCGT",
    ("oil/gas", "internal combustion"): "OCGT",
    ("oil/gas", None): "OCGT",  # fallback for unknown gas tech
    # Wind
    ("wind", "Onshore"): "onwind",
    ("wind", "Offshore hard mount"): "offwind",
    ("wind", "Offshore floating"): "offwind",
    ("wind", None): "onwind",  # fallback
    # Solar
    ("solar", "PV"): "solar",
    ("solar", "Assumed PV"): "solar",
    ("solar", "Solar Thermal"): "solar",
    ("solar", None): "solar",  # fallback
    # Hydro
    ("hydropower", "pumped storage"): "PHS",
    ("hydropower", "conventional storage"): "hydro",
    ("hydropower", "run-of-river"): "hydro",
    ("hydropower", None): "hydro",  # fallback
    # Nuclear
    ("nuclear", None): "nuclear",
    # Bioenergy
    ("bioenergy", None): "biomass",
}


def find_gem_file(search_paths: list[Path] | None = None) -> Path | None:
    """Find a GEM Excel file in the given or default search paths.

    Returns the first .xlsx file matching 'Global-Integrated-Power*' found,
    or None if no file is found.
    """
    paths = search_paths or DEFAULT_PATHS
    for directory in paths:
        if not directory.is_dir():
            continue
        matches = sorted(directory.glob("Global-Integrated-Power*.xlsx"))
        if matches:
            return matches[-1]  # newest by name
    return None


def load_gem_excel(path: Path) -> pd.DataFrame:
    """Load the GEM Excel file and return the power facilities sheet."""
    logger.info(f"Loading GEM data from {path}")
    df = pd.read_excel(path, sheet_name="Power facilities")
    logger.info(f"Loaded {len(df)} power facility records")
    return df


def filter_guangdong(df: pd.DataFrame, province: str = PROVINCE) -> pd.DataFrame:
    """Filter to operating plants in the given province."""
    col = "Subnational unit (state, province)"
    mask = (df[col] == province) & (df["Status"] == "operating")
    result = df[mask].copy()
    logger.info(
        f"Filtered to {len(result)} operating facilities in {province}"
    )
    return result


def _map_carrier(gem_type: str, technology: str | None) -> str | None:
    """Map a GEM Type + Technology pair to a PyPSA carrier name."""
    gem_type_lower = gem_type.lower().strip()
    tech_lower = technology.strip() if isinstance(technology, str) else None

    # Try exact match first
    key = (gem_type_lower, tech_lower)
    if key in _TECH_MAP:
        return _TECH_MAP[key]

    # Try type-only fallback
    key_fallback = (gem_type_lower, None)
    if key_fallback in _TECH_MAP:
        return _TECH_MAP[key_fallback]

    logger.warning(f"Unmapped GEM type/technology: {gem_type!r} / {technology!r}")
    return None


def map_technologies(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'carrier' column by mapping GEM Type/Technology to PyPSA carriers."""
    df = df.copy()
    df["carrier"] = df.apply(
        lambda row: _map_carrier(row["Type"], row.get("Technology")), axis=1
    )
    unmapped = df["carrier"].isna().sum()
    if unmapped:
        logger.warning(f"{unmapped} facilities could not be mapped to a carrier")
    return df


def get_capacity_by_carrier(df: pd.DataFrame) -> dict[str, float]:
    """Aggregate capacity in GW by carrier from mapped GEM data.

    Args:
        df: DataFrame with 'carrier' and 'Capacity (MW)' columns.

    Returns:
        Dict of carrier -> capacity in GW.
    """
    mapped = df.dropna(subset=["carrier"])
    cap = mapped.groupby("carrier")["Capacity (MW)"].sum() / 1000  # MW -> GW
    result = cap.to_dict()
    return result


def load_gem_capacities(
    gem_path: Path | None = None,
) -> dict[str, float] | None:
    """Load GEM data and return operating capacities for Guangdong by carrier.

    This is the main entry point. It finds or uses the provided GEM file,
    loads it, filters to Guangdong operating plants, maps technologies,
    and returns capacities in GW.

    Args:
        gem_path: Explicit path to GEM Excel file, or None to auto-detect.

    Returns:
        Dict of carrier -> capacity in GW, or None if no GEM data available.
    """
    path = gem_path or find_gem_file()
    if path is None:
        logger.info("No GEM data file found")
        return None
    if not path.exists():
        logger.warning(f"GEM file not found: {path}")
        return None

    try:
        df = load_gem_excel(path)
        df = filter_guangdong(df)
        df = map_technologies(df)
        capacities = get_capacity_by_carrier(df)
        logger.info(f"GEM capacities loaded: {capacities}")
        return capacities
    except Exception as e:
        logger.error(f"Failed to load GEM data: {e}")
        return None

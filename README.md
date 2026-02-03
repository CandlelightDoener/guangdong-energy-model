# Guangdong Province Energy System Model

A PyPSA-based energy system model for Guangdong Province, China, covering electricity generation, storage, and primary energy consumption.

## Features

- **Multi-sector modeling**: Electricity, heat, and primary energy carriers
- **Generation mix**: Coal, gas, nuclear, hydro, solar, wind, biomass
- **Energy storage**: Battery and pumped hydro storage
- **Regional modeling**: Optional multi-region mode with transmission lines
- **Inter-provincial imports**: West-East Power Transfer from Yunnan/Guizhou

## Installation

Requires Python 3.10+ and [uv](https://github.com/astral-sh/uv).

```bash
# Clone repository with submodules
git clone --recurse-submodules https://github.com/CandlelightDoener/guangdong-energy-model.git
cd guangdong-energy-model

# Install dependencies
uv sync
```

### GEM Power Plant Data (Capacity)

The model uses real installed capacity data from the [Global Energy Monitor (GEM)](https://globalenergymonitor.org/projects/global-integrated-power-tracker/) Global Integrated Power Tracker.

1. Download the Excel file from https://globalenergymonitor.org/projects/global-integrated-power-tracker/download-data/
2. Save it in the `data/` directory (files matching `Global-Integrated-Power*.xlsx` are auto-detected)
3. Or pass the path explicitly: `--gem-file path/to/file.xlsx`

The GEM data file is **not included** in this repository. Users must download it themselves.

> **Citation**: "Global Integrated Power Tracker, Global Energy Monitor, January 2026 release."
> Copyright Global Energy Monitor. Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

### PyPSA-China-PIK Data (Demand)

Demand and load profile data comes from [PyPSA-China-PIK](https://github.com/pik-piam/PyPSA-China-PIK). To get the latest data:

```bash
git submodule update --remote
```

## Usage

### Command Line

```bash
# Run default model (24h simulation, auto-detects GEM data in data/)
uv run guangdong-model

# Explicit GEM data file
uv run guangdong-model --gem-file data/Global-Integrated-Power-January-2026.xlsx

# Full year with GEM data
uv run guangdong-model --full-year --gem-file data/Global-Integrated-Power-January-2026.xlsx

# Multi-region model with transmission
uv run guangdong-model --multi-region

# Week-long simulation
uv run guangdong-model --snapshots 168

# Export to NetCDF
uv run guangdong-model --export-nc
```

### Python API

```python
from guangdong_energy_model import model, visualize, data

# Create network
network = model.create_network(
    snapshots=24,
    multi_region=False,
    include_storage=True,
)

# Solve optimization
network = model.solve_network(network, solver_name="highs")

# Get results
summary = model.get_generation_summary(network)
emissions = model.get_emissions_summary(network)

# Create visualizations
visualize.create_summary_report(network, "output/")
```

## Model Data

The model uses real data from [PyPSA-China-PIK](https://github.com/pik-piam/PyPSA-China-PIK) (Potsdam Institute for Climate Impact Research):

| Component | Value | Source |
|-----------|-------|--------|
| Nuclear capacity | 16.1 GW | PyPSA-China-PIK |
| Annual electricity demand (2025) | 912 TWh | PyPSA-China-PIK |
| Peak load | 110.8 GW | Hourly load data |
| Hourly load profile | 8760 hours | PyPSA-China-PIK |

### Generation Capacity (GW) — with GEM data

| Source | Capacity | Data Source |
|--------|----------|-------------|
| Coal | 71.4 | **GEM** |
| CCGT | 57.4 | **GEM** |
| Solar | 16.6 | **GEM** |
| Nuclear | 16.2 | **GEM** |
| Pumped Hydro (PHS) | 10.9 | **GEM** |
| Offshore Wind | 10.1 | **GEM** |
| Onshore Wind | 5.2 | **GEM** |
| Biomass | 4.3 | **GEM** |
| Hydro (conventional) | 1.8 | **GEM** |
| OCGT | 1.1 | **GEM** |

Data from [Global Energy Monitor](https://globalenergymonitor.org/) Global Integrated Power Tracker (January 2026 release). Without GEM data, the model falls back to rough estimates.

## Output

The model generates visualizations in the `output/` directory:
- `generation_dispatch.png` - Stacked area chart of hourly generation
- `generation_mix.png` - Pie chart of energy mix
- `load_profile.png` - Electricity demand profile
- `storage_operation.png` - Battery and pumped hydro operation
- `capacity_generation.png` - Installed capacity vs. actual generation

## License

MIT

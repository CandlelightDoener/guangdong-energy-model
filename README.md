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

### Update Real Data

The model uses real data from [PyPSA-China-PIK](https://github.com/pik-piam/PyPSA-China-PIK). To get the latest data:

```bash
git submodule update --remote
```

## Usage

### Command Line

```bash
# Run default model (24h simulation)
uv run guangdong-model

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

### Generation Capacity (GW)

| Source | Capacity | Data Source |
|--------|----------|-------------|
| Coal | 65.0 | Estimated |
| Solar | 35.0 | Estimated |
| Gas | 25.0 | Estimated |
| Nuclear | 16.1 | **Real data** |
| Hydro | 12.0 | Estimated |
| Wind | 12.0 | Estimated |
| Biomass | 3.0 | Estimated |

**Note**: Nuclear capacity and load data are from PyPSA-China-PIK. Other capacity values are estimates that can be updated as more data becomes available.

## Output

The model generates visualizations in the `output/` directory:
- `generation_dispatch.png` - Stacked area chart of hourly generation
- `generation_mix.png` - Pie chart of energy mix
- `load_profile.png` - Electricity demand profile
- `storage_operation.png` - Battery and pumped hydro operation
- `capacity_generation.png` - Installed capacity vs. actual generation

## License

MIT

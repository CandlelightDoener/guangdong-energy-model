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
# Clone repository
git clone https://github.com/YOUR_USERNAME/guangdong-energy-model.git
cd guangdong-energy-model

# Install dependencies
uv sync
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

The model uses estimated data for Guangdong Province (2023):

| Component | Value |
|-----------|-------|
| Total installed capacity | 168 GW |
| Peak load | 145 GW |
| Annual electricity demand | 800 TWh |
| Primary energy consumption | 9,580 PJ |

### Generation Capacity (GW)

| Source | Capacity |
|--------|----------|
| Coal | 65.0 |
| Solar | 35.0 |
| Gas | 25.0 |
| Nuclear | 16.0 |
| Hydro | 12.0 |
| Wind | 12.0 |
| Biomass | 3.0 |

**Note**: These are placeholder values for demonstration. For production use, replace with verified data from official sources (China Statistical Yearbook, Guangdong Energy Administration).

## Output

The model generates visualizations in the `output/` directory:
- `generation_dispatch.png` - Stacked area chart of hourly generation
- `generation_mix.png` - Pie chart of energy mix
- `load_profile.png` - Electricity demand profile
- `storage_operation.png` - Battery and pumped hydro operation
- `capacity_generation.png` - Installed capacity vs. actual generation

## License

MIT

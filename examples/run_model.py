#!/usr/bin/env python
"""
Example script demonstrating how to use the Guangdong Energy Model.

Run with: uv run python examples/run_model.py
"""

from guangdong_energy_model import model, visualize, data
from pathlib import Path


def main():
    print("Guangdong Province Energy System - Example Run")
    print("=" * 50)

    # Show primary energy data
    print("\n1. Primary Energy Consumption (PJ/year):")
    for source, pj in data.PRIMARY_ENERGY_PJ.items():
        print(f"   {source:12s}: {pj:,} PJ")
    total_pj = sum(data.PRIMARY_ENERGY_PJ.values())
    print(f"   {'TOTAL':12s}: {total_pj:,} PJ")

    # Show electricity demand by sector
    print("\n2. Electricity Demand by Sector (TWh/year):")
    for sector, twh in data.ELECTRICITY_DEMAND_TWH.items():
        print(f"   {sector:12s}: {twh:,} TWh")
    total_twh = sum(data.ELECTRICITY_DEMAND_TWH.values())
    print(f"   {'TOTAL':12s}: {total_twh:,} TWh")

    # Create network
    print("\n3. Creating PyPSA Network...")
    network = model.create_network(
        snapshots=24,  # 24 hours
        multi_region=False,
        include_storage=True,
    )

    print(f"   Buses: {len(network.buses)}")
    print(f"   Generators: {len(network.generators)}")
    print(f"   Storage units: {len(network.storage_units)}")

    # Show installed capacity
    print("\n4. Installed Generation Capacity (GW):")
    for gen_type, gw in data.INSTALLED_CAPACITY_GW.items():
        print(f"   {gen_type:12s}: {gw:.1f} GW")

    # Solve network
    print("\n5. Running Optimization...")
    try:
        network = model.solve_network(network, solver_name="highs")
        print("   Optimization successful!")

        # Results
        summary = model.get_generation_summary(network)
        print("\n6. Generation Results:")
        print(summary.to_string())

        emissions = model.get_emissions_summary(network)
        print(f"\n7. CO2 Emissions:")
        print(f"   Total: {emissions['total_co2_tonnes']:,.0f} tonnes")
        print(f"   Intensity: {emissions['co2_intensity_kg_mwh']:.1f} kg/MWh")

        # Save visualizations
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        visualize.create_summary_report(network, output_dir)
        print(f"\n8. Visualizations saved to: {output_dir.absolute()}")

    except Exception as e:
        print(f"   Optimization failed: {e}")
        print("   Install solver: uv add highspy")

    print("\n" + "=" * 50)
    print("Done!")


if __name__ == "__main__":
    main()

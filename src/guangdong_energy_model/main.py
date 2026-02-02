"""
Main entry point for Guangdong Energy System Model.

Run with: uv run guangdong-model
Or: python -m guangdong_energy_model.main
"""

import argparse
from pathlib import Path

from . import model, visualize


def main():
    parser = argparse.ArgumentParser(
        description="Guangdong Province Energy System Model"
    )
    parser.add_argument(
        "--multi-region",
        action="store_true",
        help="Use multi-regional model with transmission",
    )
    parser.add_argument(
        "--no-storage",
        action="store_true",
        help="Exclude energy storage from model",
    )
    parser.add_argument(
        "--snapshots",
        type=int,
        default=24,
        help="Number of hourly time steps (default: 24)",
    )
    parser.add_argument(
        "--solver",
        type=str,
        default="highs",
        choices=["highs", "glpk", "gurobi", "cplex"],
        help="Optimization solver to use (default: highs)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for output files (default: output)",
    )
    parser.add_argument(
        "--no-solve",
        action="store_true",
        help="Create network without solving (for inspection)",
    )
    parser.add_argument(
        "--export-nc",
        action="store_true",
        help="Export network to NetCDF file",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Guangdong Province Energy System Model")
    print("=" * 60)

    # Create network
    print("\nCreating network...")
    network = model.create_network(
        snapshots=args.snapshots,
        multi_region=args.multi_region,
        include_storage=not args.no_storage,
    )

    # Print network summary
    print(f"\nNetwork Summary:")
    print(f"  Buses: {len(network.buses)}")
    print(f"  Generators: {len(network.generators)}")
    print(f"  Loads: {len(network.loads)}")
    print(f"  Storage Units: {len(network.storage_units)}")
    print(f"  Lines: {len(network.lines)}")
    print(f"  Snapshots: {len(network.snapshots)}")

    # Print capacity summary
    print(f"\nInstalled Capacity by Carrier (GW):")
    cap_by_carrier = network.generators.groupby("carrier").p_nom.sum() / 1000
    for carrier, cap in cap_by_carrier.items():
        print(f"  {carrier:15s}: {cap:8.1f} GW")
    print(f"  {'TOTAL':15s}: {cap_by_carrier.sum():8.1f} GW")

    # Print load summary
    total_load = network.loads_t.p_set.sum(axis=1)
    print(f"\nLoad Summary:")
    print(f"  Peak Load: {total_load.max()/1000:.1f} GW")
    print(f"  Min Load: {total_load.min()/1000:.1f} GW")
    print(f"  Total Demand: {total_load.sum()/1000:.1f} GWh")

    if not args.no_solve:
        # Solve network
        print(f"\nSolving with {args.solver}...")
        try:
            network = model.solve_network(network, solver_name=args.solver)
            print("Optimization completed successfully!")

            # Print results
            gen_summary = model.get_generation_summary(network)
            if not gen_summary.empty:
                print("\nGeneration Summary:")
                print(gen_summary.to_string())

            emissions = model.get_emissions_summary(network)
            if emissions:
                print(f"\nEmissions:")
                print(f"  Total CO2: {emissions['total_co2_tonnes']:,.0f} tonnes")
                print(f"  CO2 Intensity: {emissions['co2_intensity_kg_mwh']:.1f} kg/MWh")

            costs = model.get_cost_summary(network)
            if costs:
                print(f"\nCosts:")
                print(f"  Total Cost: {costs['total_cost_cny']:,.0f} CNY")
                print(f"  Average Cost: {costs['avg_cost_cny_mwh']:.2f} CNY/MWh")

            # Generate visualizations
            args.output_dir.mkdir(parents=True, exist_ok=True)
            print(f"\nGenerating visualizations in {args.output_dir}...")
            visualize.create_summary_report(network, args.output_dir)

        except Exception as e:
            print(f"Optimization failed: {e}")
            print("Try installing a solver: pip install highspy")

    # Export network
    if args.export_nc:
        nc_path = args.output_dir / "guangdong_network.nc"
        network.export_to_netcdf(nc_path)
        print(f"\nNetwork exported to {nc_path}")

    print("\n" + "=" * 60)
    print("Done!")

    return network


if __name__ == "__main__":
    main()

"""
Visualization functions for Guangdong Energy System Model.
"""

import pypsa
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Color scheme for energy carriers
CARRIER_COLORS = {
    "coal": "#4a4a4a",
    "gas": "#ff9933",
    "nuclear": "#ff66cc",
    "hydro": "#3399ff",
    "solar": "#ffcc00",
    "wind": "#66cc66",
    "biomass": "#996633",
    "import_hydro": "#99ccff",
    "battery": "#9966ff",
    "pumped_hydro": "#6699ff",
}


def plot_generation_dispatch(
    network: pypsa.Network,
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Plot stacked area chart of generation dispatch over time.

    Args:
        network: Solved PyPSA network
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure
    """
    if network.generators_t.p.empty:
        raise ValueError("Network has no generation results. Run solve first.")

    # Group by carrier
    gen_by_carrier = network.generators_t.p.T.groupby(
        network.generators.carrier
    ).sum().T

    # Sort by baseload to peak
    merit_order = ["nuclear", "import_hydro", "hydro", "solar", "wind",
                   "biomass", "coal", "gas"]
    cols = [c for c in merit_order if c in gen_by_carrier.columns]
    gen_by_carrier = gen_by_carrier[cols]

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = [CARRIER_COLORS.get(c, "#999999") for c in gen_by_carrier.columns]
    gen_by_carrier.plot.area(ax=ax, color=colors, alpha=0.8, linewidth=0)

    # Add load line
    total_load = network.loads_t.p_set.sum(axis=1)
    ax.plot(total_load.index, total_load.values, "k--", linewidth=2, label="Load")

    ax.set_xlabel("Time")
    ax.set_ylabel("Power (MW)")
    ax.set_title("Guangdong Province - Generation Dispatch")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_generation_mix(
    network: pypsa.Network,
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Plot pie chart of generation mix.

    Args:
        network: Solved PyPSA network
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure
    """
    if network.generators_t.p.empty:
        raise ValueError("Network has no generation results. Run solve first.")

    gen_by_carrier = network.generators_t.p.T.groupby(
        network.generators.carrier
    ).sum().sum(axis=1)

    # Filter out zero values
    gen_by_carrier = gen_by_carrier[gen_by_carrier > 0]

    fig, ax = plt.subplots(figsize=(10, 8))

    colors = [CARRIER_COLORS.get(c, "#999999") for c in gen_by_carrier.index]

    wedges, texts, autotexts = ax.pie(
        gen_by_carrier.values,
        labels=gen_by_carrier.index,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        explode=[0.02] * len(gen_by_carrier),
    )

    ax.set_title("Guangdong Province - Generation Mix")

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_capacity_vs_generation(
    network: pypsa.Network,
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Plot comparison of installed capacity vs actual generation.

    Args:
        network: Solved PyPSA network
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure
    """
    # Capacity by carrier
    capacity = network.generators.groupby("carrier").p_nom.sum() / 1000  # GW

    # Generation by carrier (GWh)
    if not network.generators_t.p.empty:
        generation = network.generators_t.p.T.groupby(
            network.generators.carrier
        ).sum().sum(axis=1) / 1000  # GWh
    else:
        generation = pd.Series(0, index=capacity.index)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Capacity bar chart
    colors = [CARRIER_COLORS.get(c, "#999999") for c in capacity.index]
    capacity.plot.bar(ax=axes[0], color=colors, edgecolor="black")
    axes[0].set_xlabel("Carrier")
    axes[0].set_ylabel("Installed Capacity (GW)")
    axes[0].set_title("Installed Capacity by Source")
    axes[0].tick_params(axis="x", rotation=45)

    # Generation bar chart
    if generation.sum() > 0:
        colors = [CARRIER_COLORS.get(c, "#999999") for c in generation.index]
        generation.plot.bar(ax=axes[1], color=colors, edgecolor="black")
        axes[1].set_xlabel("Carrier")
        axes[1].set_ylabel("Generation (GWh)")
        axes[1].set_title("Generation by Source (Simulation Period)")
        axes[1].tick_params(axis="x", rotation=45)
    else:
        axes[1].text(0.5, 0.5, "Run optimization first",
                     ha="center", va="center", transform=axes[1].transAxes)
        axes[1].set_title("Generation by Source")

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_storage_operation(
    network: pypsa.Network,
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Plot storage unit charging/discharging and state of charge.

    Args:
        network: Solved PyPSA network
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure
    """
    if network.storage_units_t.p.empty:
        raise ValueError("Network has no storage results. Run solve first.")

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Power dispatch (positive = discharge, negative = charge)
    storage_p = network.storage_units_t.p
    colors = [CARRIER_COLORS.get(
        network.storage_units.loc[s, "carrier"], "#999999"
    ) for s in storage_p.columns]

    storage_p.plot(ax=axes[0], color=colors, linewidth=2)
    axes[0].axhline(0, color="black", linestyle="-", linewidth=0.5)
    axes[0].set_ylabel("Power (MW)\n(+discharge / -charge)")
    axes[0].set_title("Storage Operation")
    axes[0].legend(loc="upper right")
    axes[0].grid(True, alpha=0.3)

    # State of charge
    if not network.storage_units_t.state_of_charge.empty:
        soc = network.storage_units_t.state_of_charge
        soc.plot(ax=axes[1], color=colors, linewidth=2)
        axes[1].set_ylabel("State of Charge (MWh)")
        axes[1].set_xlabel("Time")
        axes[1].legend(loc="upper right")
        axes[1].grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_load_profile(
    network: pypsa.Network,
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Plot load profile over time.

    Args:
        network: PyPSA network
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(12, 5))

    total_load = network.loads_t.p_set.sum(axis=1)
    ax.fill_between(total_load.index, 0, total_load.values,
                    alpha=0.6, color="#cc3333")
    ax.plot(total_load.index, total_load.values, color="#cc3333", linewidth=2)

    ax.set_xlabel("Time")
    ax.set_ylabel("Load (MW)")
    ax.set_title("Guangdong Province - Electricity Demand Profile")
    ax.grid(True, alpha=0.3)

    # Add peak annotation
    peak_idx = total_load.idxmax()
    peak_val = total_load.max()
    ax.annotate(
        f"Peak: {peak_val/1000:.1f} GW",
        xy=(peak_idx, peak_val),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=10,
        arrowprops=dict(arrowstyle="->", color="black"),
    )

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def create_summary_report(
    network: pypsa.Network,
    output_dir: Path,
) -> None:
    """
    Create a comprehensive summary report with all visualizations.

    Args:
        network: Solved PyPSA network
        output_dir: Directory to save report files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate all plots
    plot_load_profile(network, output_dir / "load_profile.png")
    plot_capacity_vs_generation(network, output_dir / "capacity_generation.png")

    if not network.generators_t.p.empty:
        plot_generation_dispatch(network, output_dir / "generation_dispatch.png")
        plot_generation_mix(network, output_dir / "generation_mix.png")

    if not network.storage_units_t.p.empty:
        plot_storage_operation(network, output_dir / "storage_operation.png")

    print(f"Report saved to {output_dir}")

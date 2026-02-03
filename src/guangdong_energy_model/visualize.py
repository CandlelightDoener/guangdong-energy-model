"""
Visualization functions for Guangdong Energy System Model.
"""

import pypsa
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from . import data

# Color scheme for energy carriers
CARRIER_COLORS = {
    "coal": "#4a4a4a",
    "gas": "#ff9933",
    "CCGT": "#ff9933",
    "OCGT": "#ffbb66",
    "nuclear": "#ff66cc",
    "hydro": "#3399ff",
    "PHS": "#6699ff",
    "solar": "#ffcc00",
    "wind": "#66cc66",
    "onwind": "#66cc66",
    "offwind": "#339966",
    "biomass": "#996633",
    "import_hydro": "#99ccff",
    "battery": "#9966ff",
    "pumped_hydro": "#6699ff",
}


def _source_label() -> str:
    """Return a data source attribution string for plot annotations."""
    parts = []
    if data.is_using_gem_data():
        parts.append("Capacity: Global Energy Monitor (GEM)")
    else:
        parts.append("Capacity: Placeholder estimates")
    if data.is_using_real_data():
        parts.append("Demand: PyPSA-China-PIK")
    else:
        parts.append("Demand: Placeholder estimates")
    return "Data — " + " | " .join(parts)


def _add_source(fig: plt.Figure) -> None:
    """Add a small data-source footnote to the bottom of a figure."""
    fig.text(
        0.01, 0.005, _source_label(),
        fontsize=7, color="#888888", style="italic",
    )


def _sim_period(network: pypsa.Network) -> str:
    """Return a human-readable string describing the simulation time span."""
    s = network.snapshots
    t0, t1 = s[0], s[-1]
    n = len(s)
    if n >= 8760:
        return f"full year, {t0:%Y}"
    elif n >= 720:
        return f"{t0:%b %Y} – {t1:%b %Y}"
    elif n > 24:
        return f"{t0:%Y-%m-%d} – {t1:%Y-%m-%d} ({n} h)"
    else:
        return f"{t0:%Y-%m-%d} ({n} h)"


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
    merit_order = ["nuclear", "import_hydro", "hydro", "PHS", "solar",
                   "wind", "onwind", "offwind", "biomass", "coal",
                   "gas", "CCGT", "OCGT"]
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
    ax.set_title(f"Guangdong Province — Generation Dispatch ({_sim_period(network)})")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    _add_source(fig)

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

    ax.set_title(f"Guangdong Province — Generation Mix ({_sim_period(network)})")
    _add_source(fig)

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
    period = _sim_period(network)
    axes[0].set_xlabel("Carrier")
    axes[0].set_ylabel("Installed Capacity (GW)")
    axes[0].set_title("Guangdong — Installed Capacity by Source")
    axes[0].tick_params(axis="x", rotation=45)

    # Generation bar chart
    if generation.sum() > 0:
        colors = [CARRIER_COLORS.get(c, "#999999") for c in generation.index]
        generation.plot.bar(ax=axes[1], color=colors, edgecolor="black")
        axes[1].set_xlabel("Carrier")
        axes[1].set_ylabel("Generation (GWh)")
        axes[1].set_title(f"Guangdong — Generation by Source ({period})")
        axes[1].tick_params(axis="x", rotation=45)
    else:
        axes[1].text(0.5, 0.5, "Run optimization first",
                     ha="center", va="center", transform=axes[1].transAxes)
        axes[1].set_title("Guangdong — Generation by Source")

    plt.tight_layout()
    _add_source(fig)

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
    axes[0].set_title(f"Guangdong — Storage Operation ({_sim_period(network)})")
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
    _add_source(fig)

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
    ax.set_title(f"Guangdong Province — Electricity Demand ({_sim_period(network)})")
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
    _add_source(fig)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_monthly_generation(
    monthly_gen: pd.DataFrame,
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Plot monthly generation by carrier as stacked bar chart.

    Args:
        monthly_gen: DataFrame with monthly generation by carrier (from model.get_monthly_generation)
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(14, 7))

    # Reorder columns by total generation (baseload first)
    col_order = monthly_gen.sum().sort_values(ascending=False).index.tolist()
    monthly_gen = monthly_gen[col_order]

    colors = [CARRIER_COLORS.get(c, "#999999") for c in monthly_gen.columns]

    monthly_gen.plot.bar(
        ax=ax,
        stacked=True,
        color=colors,
        edgecolor="white",
        linewidth=0.5,
    )

    ax.set_xlabel("Month")
    ax.set_ylabel("Generation (TWh)")
    ax.set_title("Guangdong Province — Monthly Generation by Source")
    ax.legend(title="Source", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.grid(True, alpha=0.3, axis="y")

    # Rotate x labels
    plt.xticks(rotation=0)

    plt.tight_layout()
    _add_source(fig)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_monthly_energy_mix(
    monthly_gen: pd.DataFrame,
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Plot monthly energy mix as percentage stacked area chart.

    Args:
        monthly_gen: DataFrame with monthly generation by carrier
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(14, 7))

    # Calculate percentages
    monthly_pct = monthly_gen.div(monthly_gen.sum(axis=1), axis=0) * 100

    # Reorder columns
    col_order = monthly_gen.sum().sort_values(ascending=False).index.tolist()
    monthly_pct = monthly_pct[col_order]

    colors = [CARRIER_COLORS.get(c, "#999999") for c in monthly_pct.columns]

    monthly_pct.plot.area(
        ax=ax,
        stacked=True,
        color=colors,
        alpha=0.8,
        linewidth=0,
    )

    ax.set_xlabel("Month")
    ax.set_ylabel("Share (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Guangdong Province — Monthly Energy Mix (%)")
    ax.legend(title="Source", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    _add_source(fig)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_yearly_summary(
    yearly_stats: dict,
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Plot yearly summary with generation mix pie and key statistics.

    Args:
        yearly_stats: Dictionary from model.get_yearly_statistics()
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Pie chart of generation mix
    gen_mix = yearly_stats.get("generation_mix_pct", {})
    if gen_mix:
        labels = list(gen_mix.keys())
        sizes = list(gen_mix.values())
        colors = [CARRIER_COLORS.get(c, "#999999") for c in labels]

        axes[0].pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
        )
        axes[0].set_title("Guangdong — Annual Generation Mix")

    # Key statistics as text
    stats_text = f"""
    GUANGDONG — YEARLY STATISTICS
    {"="*30}

    Generation: {yearly_stats.get('total_generation_twh', 0):.1f} TWh
    Demand:     {yearly_stats.get('total_demand_twh', 0):.1f} TWh

    Peak Load:  {yearly_stats.get('peak_demand_gw', 0):.1f} GW
    Min Load:   {yearly_stats.get('min_demand_gw', 0):.1f} GW

    CO₂ Emissions: {yearly_stats.get('total_co2_mt', 0):.1f} Mt
    CO₂ Intensity: {yearly_stats.get('co2_intensity_kg_mwh', 0):.0f} kg/MWh

    CAPACITY FACTORS
    {"="*30}
    """
    cf = yearly_stats.get("capacity_factors", {})
    for carrier, factor in sorted(cf.items(), key=lambda x: -x[1]):
        stats_text += f"\n    {carrier:15s}: {factor*100:5.1f}%"

    axes[1].text(0.1, 0.9, stats_text, transform=axes[1].transAxes,
                 fontsize=11, verticalalignment="top", fontfamily="monospace")
    axes[1].axis("off")
    axes[1].set_title("Key Statistics")

    plt.tight_layout()
    _add_source(fig)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def create_summary_report(
    network: pypsa.Network,
    output_dir: Path,
    yearly_stats: dict | None = None,
    monthly_gen: pd.DataFrame | None = None,
) -> None:
    """
    Create a comprehensive summary report with all visualizations.

    Args:
        network: Solved PyPSA network
        output_dir: Directory to save report files
        yearly_stats: Optional yearly statistics from model.get_yearly_statistics()
        monthly_gen: Optional monthly generation from model.get_monthly_generation()
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate basic plots
    plot_load_profile(network, output_dir / "load_profile.png")
    plot_capacity_vs_generation(network, output_dir / "capacity_generation.png")

    if not network.generators_t.p.empty:
        plot_generation_dispatch(network, output_dir / "generation_dispatch.png")
        plot_generation_mix(network, output_dir / "generation_mix.png")

    if not network.storage_units_t.p.empty:
        plot_storage_operation(network, output_dir / "storage_operation.png")

    # Generate yearly/monthly plots if data provided
    if yearly_stats:
        plot_yearly_summary(yearly_stats, output_dir / "yearly_summary.png")

    if monthly_gen is not None and not monthly_gen.empty:
        plot_monthly_generation(monthly_gen, output_dir / "monthly_generation.png")
        plot_monthly_energy_mix(monthly_gen, output_dir / "monthly_energy_mix.png")

    print(f"Report saved to {output_dir}")

"""Plot race lap times against tyre age for three Bahrain drivers."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MPL_CONFIG_DIR = PROJECT_ROOT / "data" / "cache" / "matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

import matplotlib.pyplot as plt
import pandas as pd

from explore_race_data import add_tyre_info_to_laps
from load_race_session import CACHE_DIR, load_race_session


OUTPUT_PATH = PROJECT_ROOT / "reports" / "lap_time_vs_tyre_age.png"
DRIVER_LABELS = {
    1: "Max Verstappen (#1)",
    16: "Charles Leclerc (#16)",
    44: "Lewis Hamilton (#44)",
}
COMPOUND_COLORS = {
    "SOFT": "#e10600",
    "MEDIUM": "#f5c400",
    "HARD": "#aeb4bc",
}


def plot_lap_time_vs_tyre_age(
    laps: pd.DataFrame,
    driver_numbers: list[int],
    output_path: Path,
) -> int:
    """Save one lap-time-versus-age scatter plot for each selected driver."""
    selected_laps = laps.loc[laps["driver_number"].isin(driver_numbers)]
    valid_laps = selected_laps.dropna(
        subset=["lap_duration", "tyre_age", "compound"]
    )

    # Pit-stop and outlaps include time spent entering or leaving the pit lane.
    clean_laps = valid_laps.loc[
        ~valid_laps["is_pit_stop_lap"] & ~valid_laps["is_pit_out_lap"]
    ]
    removed_count = len(selected_laps) - len(clean_laps)

    figure, axes_grid = plt.subplots(
        nrows=1,
        ncols=len(driver_numbers),
        figsize=(15, 4.5),
        sharey=True,
        squeeze=False,
    )
    axes = axes_grid[0]

    for axis, driver_number in zip(axes, driver_numbers):
        driver_laps = clean_laps.loc[
            clean_laps["driver_number"].eq(driver_number)
        ]
        for compound, color in COMPOUND_COLORS.items():
            compound_laps = driver_laps.loc[
                driver_laps["compound"].eq(compound)
            ]
            if not compound_laps.empty:
                axis.scatter(
                    compound_laps["tyre_age"],
                    compound_laps["lap_duration"],
                    color=color,
                    label=compound,
                    s=24,
                    alpha=0.75,
                    edgecolors="none",
                )

        axis.set_title(DRIVER_LABELS.get(driver_number, f"Driver #{driver_number}"))
        axis.set_xlabel("Tyre age (laps)")
        axis.grid(True, alpha=0.25)

    axes[0].set_ylabel("Lap time (seconds)")

    # Collect one legend entry per compound across all three driver panels.
    legend_items = {}
    for axis in axes:
        handles, labels = axis.get_legend_handles_labels()
        for handle, label in zip(handles, labels):
            legend_items.setdefault(label, handle)

    figure.suptitle("2024 Bahrain Grand Prix: Lap time vs tyre age", y=0.99)
    figure.legend(
        legend_items.values(),
        legend_items.keys(),
        title="Compound",
        loc="upper center",
        bbox_to_anchor=(0.5, 0.94),
        ncol=max(1, len(legend_items)),
    )
    figure.tight_layout(rect=(0, 0, 1, 0.83))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    print(f"Saved plot: {output_path}")
    print(f"Selected-driver lap records excluded or missing: {removed_count}")
    print(f"Selected-driver laps plotted: {len(clean_laps)}")
    return len(clean_laps)


def main() -> None:
    race = load_race_session(
        year=2024,
        country_name="Bahrain",
        session_name="Race",
        cache_dir=CACHE_DIR,
    )
    laps_with_tyres = add_tyre_info_to_laps(
        race.laps,
        race.stints,
        race.pit_stops,
    )
    plot_lap_time_vs_tyre_age(
        laps=laps_with_tyres,
        driver_numbers=list(DRIVER_LABELS),
        output_path=OUTPUT_PATH,
    )


if __name__ == "__main__":
    main()

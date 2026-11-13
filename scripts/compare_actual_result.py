"""Replay every classified Bahrain 2024 driver's observed race strategy."""

from pathlib import Path

import pandas as pd

from simulate_pit_strategy import (
    PIT_LOSS_SECONDS,
    add_compound_age_feature,
    build_strategy_model,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_cleaning_audit.csv"
COMPARISON_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_driver_comparison.csv"

# Official FIA final classification: position, driver name, completed laps, time.
# The elapsed-time values include the hours component when the race exceeds one hour.
OFFICIAL_RESULTS = {
    1: (1, "Max Verstappen", 57, "1:31:44.742"),
    11: (2, "Sergio Perez", 57, "1:32:07.199"),
    55: (3, "Carlos Sainz", 57, "1:32:09.852"),
    16: (4, "Charles Leclerc", 57, "1:32:24.411"),
    63: (5, "George Russell", 57, "1:32:31.530"),
    4: (6, "Lando Norris", 57, "1:32:33.200"),
    44: (7, "Lewis Hamilton", 57, "1:32:35.066"),
    81: (8, "Oscar Piastri", 57, "1:32:40.824"),
    14: (9, "Fernando Alonso", 57, "1:32:59.629"),
    18: (10, "Lance Stroll", 57, "1:33:17.958"),
    24: (11, "Zhou Guanyu", 56, "1:31:51.501"),
    20: (12, "Kevin Magnussen", 56, "1:31:53.058"),
    3: (13, "Daniel Ricciardo", 56, "1:31:53.700"),
    22: (14, "Yuki Tsunoda", 56, "1:31:54.224"),
    23: (15, "Alexander Albon", 56, "1:31:56.628"),
    27: (16, "Nico Hulkenberg", 56, "1:32:02.374"),
    31: (17, "Esteban Ocon", 56, "1:32:16.192"),
    10: (18, "Pierre Gasly", 56, "1:32:17.159"),
    77: (19, "Valtteri Bottas", 56, "1:33:07.972"),
    2: (20, "Logan Sargeant", 55, "1:32:05.537"),
}


def parse_race_time(value: str) -> float:
    """Convert an official H:MM:SS.mmm time string to elapsed seconds."""
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def compare_drivers(audit: pd.DataFrame) -> pd.DataFrame:
    """Use leave-one-driver-out fitting to replay each actual race strategy."""
    eligible = audit.loc[audit["keep_for_degradation_model"]].dropna(
        subset=["compound", "tyre_age", "fuel_corrected_lap_time"]
    )
    fuel_penalty_by_lap = (
        audit.groupby("lap_number")["estimated_fuel_penalty_seconds"].mean().to_dict()
    )
    comparisons: list[dict[str, float | int | str]] = []

    for driver_number, (position, driver_name, official_laps, official_time) in (
        OFFICIAL_RESULTS.items()
    ):
        driver_laps = audit.loc[audit["driver_number"].eq(driver_number)].sort_values(
            "lap_number"
        )
        if len(driver_laps) != official_laps:
            raise ValueError(
                f"Driver {driver_name} has {len(driver_laps)} stored laps; "
                f"the FIA classification lists {official_laps}. Reload the race data."
            )

        training_laps = eligible.loc[eligible["driver_number"].ne(driver_number)]
        if training_laps.empty:
            raise ValueError(f"No training laps remain after holding out {driver_name}.")

        model = build_strategy_model()
        model.fit(
            add_compound_age_feature(training_laps),
            training_laps["fuel_corrected_lap_time"],
        )
        predicted_fuel_corrected = model.predict(add_compound_age_feature(driver_laps))
        fuel_penalty = sum(
            fuel_penalty_by_lap[int(lap)]
            for lap in driver_laps["lap_number"]
        )
        stop_laps = driver_laps.loc[driver_laps["is_pit_stop_lap"], "lap_number"]
        pit_laps_after = ",".join(str(int(lap)) for lap in stop_laps)
        stint_compounds = "-".join(
            driver_laps.drop_duplicates("stint_number")["compound"].astype(str)
        )
        stint_lengths = ",".join(
            str(int(count))
            for count in driver_laps.groupby("stint_number", sort=True).size()
        )
        actual_seconds = parse_race_time(official_time)
        predicted_seconds = (
            float(predicted_fuel_corrected.sum())
            + fuel_penalty
            + len(stop_laps) * PIT_LOSS_SECONDS
        )

        comparisons.append(
            {
                "driver_number": driver_number,
                "driver_name": driver_name,
                "actual_position": position,
                "actual_laps": official_laps,
                "actual_time_seconds": actual_seconds,
                "actual_time_official": official_time,
                "actual_pit_stops": len(stop_laps),
                "actual_pit_laps_after": pit_laps_after,
                "actual_stint_compounds": stint_compounds,
                "actual_stint_lengths": stint_lengths,
                "predicted_time_seconds": predicted_seconds,
                "error_seconds": predicted_seconds - actual_seconds,
                "absolute_error_seconds": abs(predicted_seconds - actual_seconds),
            }
        )

    return pd.DataFrame(comparisons).sort_values("actual_position").reset_index(drop=True)


def main() -> None:
    if not AUDIT_PATH.exists():
        raise FileNotFoundError(
            "Cleaning audit is missing. Run scripts/clean_race_data.py first."
        )

    comparison = compare_drivers(pd.read_csv(AUDIT_PATH))
    COMPARISON_PATH.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(COMPARISON_PATH, index=False)

    errors = comparison["error_seconds"]
    mae = comparison["absolute_error_seconds"].mean()
    rmse = (errors.pow(2).mean()) ** 0.5
    mean_bias = errors.mean()
    winner_error = float(
        comparison.loc[comparison["driver_number"].eq(1), "error_seconds"].iloc[0]
    )
    print(f"Drivers compared: {len(comparison)}")
    print(f"Mean absolute error: {mae:.3f} seconds")
    print(f"Root mean squared error: {rmse:.3f} seconds")
    print(f"Mean signed error (model - actual): {mean_bias:+.3f} seconds")
    print(f"Winner replay error: {winner_error:+.3f} seconds")
    print("Driver comparison:")
    print(
        comparison[
            [
                "actual_position",
                "driver_name",
                "actual_stint_compounds",
                "actual_pit_laps_after",
                "actual_time_official",
                "predicted_time_seconds",
                "error_seconds",
            ]
        ].to_string(index=False, formatters={"predicted_time_seconds": "{:.3f}".format,
                                             "error_seconds": "{:+.3f}".format})
    )
    print(f"Saved comparison: {COMPARISON_PATH}")
    print(
        "Caution: leave-one-driver-out prevents fitting on the evaluated driver's "
        "laps, but other drivers from the same race are still in the training set. "
        "This is not a pre-race test on an unseen Grand Prix."
    )


if __name__ == "__main__":
    main()

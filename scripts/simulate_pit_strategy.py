"""Compare illustrative one-stop strategies for the 2024 Bahrain race."""

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression

from train_baseline_model import build_model


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_cleaning_audit.csv"
RESULTS_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_strategy_results.csv"
RACE_LAPS = 57
PIT_LOSS_SECONDS = 24.8
MIN_STINT_LAPS = 5
COMPOUNDS = ("HARD", "SOFT")


def load_eligible_laps() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read the cleaning audit and keep laps with usable model features."""
    if not AUDIT_PATH.exists():
        raise FileNotFoundError(
            "Cleaning audit is missing. Run scripts/clean_race_data.py first."
        )

    audit = pd.read_csv(AUDIT_PATH)
    eligible = audit.loc[audit["keep_for_degradation_model"]].copy()
    eligible = eligible.dropna(
        subset=["compound", "tyre_age", "fuel_corrected_lap_time"]
    )
    return audit, eligible


def make_stint_laps(compound: str, stint_length: int) -> pd.DataFrame:
    """Create one hypothetical lap row for every tyre age in a stint."""
    return pd.DataFrame(
        {
            "compound": [compound] * stint_length,
            "tyre_age": range(1, stint_length + 1),
        }
    )


def simulate_one_stop_strategies(
    audit: pd.DataFrame,
    eligible: pd.DataFrame,
) -> pd.DataFrame:
    """Fit the selected linear model and rank all two-compound one-stop plans."""
    features = eligible[["compound", "tyre_age"]]
    target = eligible["fuel_corrected_lap_time"]
    model = build_model(LinearRegression())
    model.fit(features, target)

    max_observed_age = eligible.groupby("compound")["tyre_age"].max().to_dict()
    fuel_penalty_by_lap = (
        audit.groupby("lap_number")["estimated_fuel_penalty_seconds"]
        .mean()
        .to_dict()
    )
    strategies: list[dict[str, float | int | str]] = []

    for first_compound in COMPOUNDS:
        second_compound = next(
            compound for compound in COMPOUNDS if compound != first_compound
        )
        for pit_lap in range(MIN_STINT_LAPS, RACE_LAPS - MIN_STINT_LAPS + 1):
            first_stint_laps = pit_lap
            second_stint_laps = RACE_LAPS - pit_lap

            first_stint = make_stint_laps(first_compound, first_stint_laps)
            second_stint = make_stint_laps(second_compound, second_stint_laps)
            predicted_fuel_corrected = model.predict(
                pd.concat([first_stint, second_stint], ignore_index=True)
            )
            estimated_fuel_penalties = [
                fuel_penalty_by_lap[lap_number]
                for lap_number in range(1, RACE_LAPS + 1)
            ]
            predicted_race_time = (
                float(predicted_fuel_corrected.sum())
                + sum(estimated_fuel_penalties)
                + PIT_LOSS_SECONDS
            )
            extrapolated_laps = sum(
                age > max_observed_age[compound]
                for compound, stint_length in (
                    (first_compound, first_stint_laps),
                    (second_compound, second_stint_laps),
                )
                for age in range(1, stint_length + 1)
            )
            strategies.append(
                {
                    "pit_lap": pit_lap,
                    "first_compound": first_compound,
                    "second_compound": second_compound,
                    "first_stint_laps": first_stint_laps,
                    "second_stint_laps": second_stint_laps,
                    "predicted_race_time_seconds": predicted_race_time,
                    "pit_loss_seconds": PIT_LOSS_SECONDS,
                    "laps_beyond_observed_tyre_age": extrapolated_laps,
                }
            )

    return pd.DataFrame(strategies).sort_values(
        "predicted_race_time_seconds"
    ).reset_index(drop=True)


def main() -> None:
    audit, eligible = load_eligible_laps()
    results = simulate_one_stop_strategies(audit, eligible)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(RESULTS_PATH, index=False)

    print(f"Strategies evaluated: {len(results)}")
    print(f"Assumed pit loss: {PIT_LOSS_SECONDS:.1f} seconds")
    print("Fastest illustrative options:")
    print(
        results.head(5).to_string(
            index=False,
            formatters={"predicted_race_time_seconds": "{:.3f}".format},
        )
    )
    print(f"Saved full ranking: {RESULTS_PATH}")
    print(
        "Warning: this prototype fits on one race and extrapolates beyond "
        "observed tyre ages; treat its ranking as illustrative."
    )


if __name__ == "__main__":
    main()

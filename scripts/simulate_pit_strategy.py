"""Compare illustrative one-stop strategies for the 2024 Bahrain race."""

from itertools import combinations, product
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_cleaning_audit.csv"
RESULTS_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_strategy_results.csv"
RACE_LAPS = 57
PIT_LOSS_SECONDS = 24.8
MIN_STINT_LAPS = 5
COMPOUNDS = ("HARD", "SOFT")
MAX_STOPS = 2


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


def add_compound_age_feature(laps: pd.DataFrame) -> pd.DataFrame:
    """Create a feature that lets Soft tyres have a different age slope."""
    result = laps[["compound", "tyre_age"]].copy()
    result["soft_tyre_age"] = result["tyre_age"].where(
        result["compound"].eq("SOFT"),
        0,
    )
    return result


def build_strategy_model() -> Pipeline:
    """Build a linear model with separate age trends for Hard and Soft."""
    preprocessing = ColumnTransformer(
        transformers=[
            (
                "compound",
                OneHotEncoder(drop="first", handle_unknown="ignore"),
                ["compound"],
            ),
            ("age_features", "passthrough", ["tyre_age", "soft_tyre_age"]),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessing),
            ("regression", LinearRegression()),
        ]
    )


def simulate_strategies(
    audit: pd.DataFrame,
    eligible: pd.DataFrame,
) -> pd.DataFrame:
    """Rank dry-race plans with one or two stops and at least two compounds."""
    features = add_compound_age_feature(eligible)
    target = eligible["fuel_corrected_lap_time"]
    model = build_strategy_model()
    model.fit(features, target)

    max_observed_age = eligible.groupby("compound")["tyre_age"].max().to_dict()
    fuel_penalty_by_lap = (
        audit.groupby("lap_number")["estimated_fuel_penalty_seconds"]
        .mean()
        .to_dict()
    )
    fuel_time_total = sum(
        fuel_penalty_by_lap[lap_number]
        for lap_number in range(1, RACE_LAPS + 1)
    )
    strategies: list[dict[str, float | int | str]] = []

    for stop_count in range(1, MAX_STOPS + 1):
        stint_count = stop_count + 1
        candidate_pit_laps = range(
            MIN_STINT_LAPS,
            RACE_LAPS - MIN_STINT_LAPS + 1,
        )
        for pit_laps in combinations(candidate_pit_laps, stop_count):
            boundaries = (0, *pit_laps, RACE_LAPS)
            stint_lengths = tuple(
                boundaries[index + 1] - boundaries[index]
                for index in range(stint_count)
            )
            if min(stint_lengths) < MIN_STINT_LAPS:
                continue

            for compounds in product(COMPOUNDS, repeat=stint_count):
                if len(set(compounds)) < 2:
                    continue

                stint_frames = [
                    make_stint_laps(compound, stint_length)
                    for compound, stint_length in zip(compounds, stint_lengths)
                ]
                strategy_laps = add_compound_age_feature(
                    pd.concat(stint_frames, ignore_index=True)
                )
                predicted_fuel_corrected = model.predict(strategy_laps)
                predicted_race_time = (
                    float(predicted_fuel_corrected.sum())
                    + fuel_time_total
                    + stop_count * PIT_LOSS_SECONDS
                )
                extrapolated_laps = sum(
                    age > max_observed_age[compound]
                    for compound, stint_length in zip(compounds, stint_lengths)
                    for age in range(1, stint_length + 1)
                )
                strategies.append(
                    {
                        "pit_stops": stop_count,
                        "pit_laps_after": ",".join(map(str, pit_laps)),
                        "stint_compounds": "-".join(compounds),
                        "stint_lengths": ",".join(map(str, stint_lengths)),
                        "predicted_race_time_seconds": predicted_race_time,
                        "pit_loss_seconds_each": PIT_LOSS_SECONDS,
                        "laps_beyond_observed_tyre_age": extrapolated_laps,
                        "within_observed_tyre_age": extrapolated_laps == 0,
                    }
                )

    return pd.DataFrame(strategies).sort_values(
        "predicted_race_time_seconds"
    ).reset_index(drop=True)


def main() -> None:
    audit, eligible = load_eligible_laps()
    results = simulate_strategies(audit, eligible)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(RESULTS_PATH, index=False)

    print(f"Strategies evaluated: {len(results)}")
    print(f"Stops evaluated: 1 to {MAX_STOPS}")
    print(f"Assumed pit loss per stop: {PIT_LOSS_SECONDS:.1f} seconds")
    print("Fastest illustrative option (may extrapolate):")
    print(
        results.head(1).to_string(
            index=False,
            formatters={"predicted_race_time_seconds": "{:.3f}".format},
        )
    )
    supported = results.loc[results["within_observed_tyre_age"]]
    if not supported.empty:
        print("Fastest option staying within observed tyre ages:")
        print(
            supported.head(1).to_string(
                index=False,
                formatters={"predicted_race_time_seconds": "{:.3f}".format},
            )
        )
    print(f"Saved full ranking: {RESULTS_PATH}")
    print(
        "Warning: the model is fitted on one race and some strategies "
        "extrapolate beyond observed tyre ages; ranking is illustrative."
    )


if __name__ == "__main__":
    main()

"""Compare the simulator replay of Verstappen's Bahrain strategy with the result."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_RESULTS_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_strategy_results.csv"
COMPARISON_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_actual_comparison.csv"

# Official FIA classification: 1:31:44.742 after 57 laps.
ACTUAL_WINNER = "Max Verstappen"
ACTUAL_FINISH_SECONDS = 1 * 3600 + 31 * 60 + 44.742
ACTUAL_PIT_LAPS = "17,37"
ACTUAL_COMPOUNDS = "SOFT-HARD-SOFT"


def build_comparison(strategy_results: pd.DataFrame) -> pd.DataFrame:
    """Compare the model's replay of the winner's exact observed plan to reality."""
    actual_plan = strategy_results.loc[
        strategy_results["pit_laps_after"].eq(ACTUAL_PIT_LAPS)
        & strategy_results["stint_compounds"].eq(ACTUAL_COMPOUNDS)
    ]
    if len(actual_plan) != 1:
        raise ValueError(
            "Could not find the winner's observed two-stop plan in the simulator output. "
            "Regenerate it with scripts/simulate_pit_strategy.py."
        )

    replay = actual_plan.iloc[0]
    best_supported = strategy_results.loc[
        strategy_results["within_observed_tyre_age"]
    ].iloc[0]
    model_seconds = float(replay["predicted_race_time_seconds"])
    error_seconds = model_seconds - ACTUAL_FINISH_SECONDS

    return pd.DataFrame(
        [
            {
                "actual_winner": ACTUAL_WINNER,
                "actual_finish_seconds": ACTUAL_FINISH_SECONDS,
                "actual_pit_laps_after": ACTUAL_PIT_LAPS,
                "actual_stint_compounds": ACTUAL_COMPOUNDS,
                "actual_stint_lengths": str(replay["stint_lengths"]),
                "model_replay_seconds": model_seconds,
                "replay_error_seconds": error_seconds,
                "replay_error_percent": error_seconds / ACTUAL_FINISH_SECONDS * 100,
                "best_supported_compounds": best_supported["stint_compounds"],
                "best_supported_pit_laps_after": best_supported["pit_laps_after"],
                "best_supported_predicted_seconds": float(
                    best_supported["predicted_race_time_seconds"]
                ),
                "best_supported_age_extrapolation_laps": int(
                    best_supported["laps_beyond_observed_tyre_age"]
                ),
            }
        ]
    )


def main() -> None:
    if not STRATEGY_RESULTS_PATH.exists():
        raise FileNotFoundError(
            "Strategy ranking is missing. Run scripts/simulate_pit_strategy.py first."
        )

    strategy_results = pd.read_csv(STRATEGY_RESULTS_PATH)
    comparison = build_comparison(strategy_results)
    COMPARISON_PATH.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(COMPARISON_PATH, index=False)

    row = comparison.iloc[0]
    print(f"Actual winner: {row['actual_winner']}")
    print(
        "Actual result: "
        f"{int(row['actual_finish_seconds'] // 3600)}:"
        f"{int(row['actual_finish_seconds'] % 3600 // 60):02d}:"
        f"{row['actual_finish_seconds'] % 60:06.3f}"
    )
    print(
        "Actual strategy replay: "
        f"{row['actual_stint_compounds']} at pit laps "
        f"{row['actual_pit_laps_after']} -> "
        f"{row['model_replay_seconds']:.3f}s"
    )
    print(
        f"Replay error: {row['replay_error_seconds']:+.3f}s "
        f"({row['replay_error_percent']:+.3f}%)"
    )
    print(f"Saved comparison: {COMPARISON_PATH}")
    print(
        "Caution: this is a retrospective, in-sample replay. The degradation "
        "model was fitted using laps from the same race, including the winner."
    )


if __name__ == "__main__":
    main()

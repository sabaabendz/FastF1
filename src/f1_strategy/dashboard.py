"""Streamlit dashboard for exploring simulated Bahrain pit strategies."""

from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STRATEGY_RESULTS_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_strategy_results.csv"
REQUIRED_COLUMNS = {
    "pit_stops",
    "pit_laps_after",
    "stint_compounds",
    "stint_lengths",
    "predicted_race_time_seconds",
    "laps_beyond_observed_tyre_age",
    "within_observed_tyre_age",
}


@st.cache_data
def load_strategy_results(file_path: Path) -> pd.DataFrame:
    """Read the simulator output once and reuse it between UI interactions."""
    results = pd.read_csv(file_path)
    missing_columns = REQUIRED_COLUMNS.difference(results.columns)
    if missing_columns:
        raise ValueError(
            "Strategy results are missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    results["first_pit_lap"] = (
        results["pit_laps_after"].astype(str).str.split(",").str[0].astype(int)
    )
    return results


def main() -> None:
    st.set_page_config(
        page_title="F1 Race Strategy Explorer",
        page_icon="🏎️",
        layout="wide",
    )
    st.title("F1 Race Strategy Explorer")
    st.caption("Bahrain Grand Prix 2024 · one-stop and two-stop simulations")
    st.warning(
        "Educational prototype: pit-loss and fuel are estimates, and some "
        "strategies extrapolate beyond tyre ages observed in this race."
    )

    if not STRATEGY_RESULTS_PATH.exists():
        st.error(
            "Strategy results are not available yet. Run the data pipeline "
            "from the project root: load the race, clean it, then run "
            "scripts/simulate_pit_strategy.py. See the README for the commands."
        )
        st.stop()

    try:
        results = load_strategy_results(STRATEGY_RESULTS_PATH)
    except (OSError, pd.errors.ParserError, ValueError) as error:
        st.error(f"Could not read the strategy results: {error}")
        st.stop()

    st.sidebar.header("Strategy filters")
    stop_options = sorted(results["pit_stops"].dropna().astype(int).unique())
    selected_stop_count = st.sidebar.selectbox(
        "Number of pit stops",
        options=stop_options,
        format_func=lambda count: f"{count} stop{'s' if count != 1 else ''}",
    )

    filtered = results.loc[results["pit_stops"].eq(selected_stop_count)].copy()
    compound_options = sorted(filtered["stint_compounds"].unique().tolist())
    selected_compounds = st.sidebar.multiselect(
        "Tyre compound order",
        options=compound_options,
        default=compound_options,
    )
    filtered = filtered.loc[filtered["stint_compounds"].isin(selected_compounds)]

    show_supported_only = st.sidebar.checkbox(
        "Only show plans within observed tyre ages",
        value=False,
        help=(
            "Hides plans where a tyre age is beyond the maximum seen in the "
            "eligible Bahrain data."
        ),
    )
    if show_supported_only:
        filtered = filtered.loc[filtered["within_observed_tyre_age"]]

    if filtered.empty:
        st.info(
            "No strategies match these filters. One-stop plans cannot stay "
            "fully within the observed tyre-age ranges for this 57-lap race."
        )
        st.stop()

    best_strategy = filtered.iloc[0]
    in_range_strategies = filtered.loc[filtered["within_observed_tyre_age"]]
    best_in_range = (
        in_range_strategies.iloc[0] if not in_range_strategies.empty else None
    )

    metric_columns = st.columns(3)
    metric_columns[0].metric("Strategies shown", f"{len(filtered):,}")
    metric_columns[1].metric(
        "Fastest estimated total",
        f"{best_strategy['predicted_race_time_seconds']:,.1f} s",
    )
    if best_in_range is None:
        metric_columns[2].metric("Fastest in-range plan", "None")
    else:
        metric_columns[2].metric(
            "Fastest in-range plan",
            f"{best_in_range['predicted_race_time_seconds']:,.1f} s",
        )

    st.subheader("Estimated race time by first pit lap")
    st.scatter_chart(
        filtered,
        x="first_pit_lap",
        y="predicted_race_time_seconds",
        color="stint_compounds",
        height=420,
    )
    st.caption(
        "Lower points indicate a faster model estimate. Colour identifies "
        "the compound sequence; extrapolated plans are included unless filtered out."
    )

    st.subheader("Ranked strategy options")
    visible_columns = [
        "pit_stops",
        "pit_laps_after",
        "stint_compounds",
        "stint_lengths",
        "predicted_race_time_seconds",
        "pit_loss_seconds_each",
        "laps_beyond_observed_tyre_age",
        "within_observed_tyre_age",
    ]
    st.dataframe(
        filtered[visible_columns].head(30),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        f"Showing the fastest 30 of {len(filtered):,} matching plans. "
        "Race-time values are estimates, not measured race outcomes."
    )


if __name__ == "__main__":
    main()

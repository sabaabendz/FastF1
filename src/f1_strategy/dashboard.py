"""Streamlit dashboard for exploring simulated Bahrain pit strategies."""

from pathlib import Path

import pandas as pd
import streamlit as st
import altair as alt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STRATEGY_RESULTS_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_strategy_results.csv"
ACTUAL_COMPARISON_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_driver_comparison.csv"
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


def format_race_time(seconds: float) -> str:
    """Format elapsed seconds as hours:minutes:seconds.milliseconds."""
    hours = int(seconds // 3600)
    minutes = int(seconds % 3600 // 60)
    remaining_seconds = seconds % 60
    return f"{hours}:{minutes:02d}:{remaining_seconds:06.3f}"


def main() -> None:
    st.set_page_config(
        page_title="F1 Race Strategy Explorer",
        page_icon="🏎️",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
        :root { --ink:#f4f3f1; --muted:#aaa9ad; --panel:#17181c; --line:#303137; --red:#e10600; }
        html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }
        .stApp { background: radial-gradient(ellipse at 78% 0%, #321514 0%, #111216 37%, #111216 100%); color:var(--ink); }
        [data-testid="stHeader"] { background:transparent; }
        [data-testid="stSidebar"] { background:#15161a; border-right:1px solid var(--line); }
        [data-testid="stSidebar"] h2 { font-size:1.05rem; letter-spacing:.02em; }
        .block-container { max-width:1440px; padding-top:2rem; padding-bottom:3rem; }
        .hero { padding:1.6rem 1.8rem 1.45rem; margin-bottom:1.3rem; border:1px solid #38383d; border-left:4px solid var(--red); border-radius:12px; background:linear-gradient(110deg,rgba(34,35,40,.96),rgba(22,22,26,.72)); }
        .eyebrow { color:#ff7772; font-family:'DM Mono',monospace; font-size:.72rem; letter-spacing:.17em; text-transform:uppercase; margin-bottom:.6rem; }
        .hero h1 { color:var(--ink); font-size:2.15rem; font-weight:800; letter-spacing:-.055em; margin:0; }
        .hero p { color:#b9b8bc; margin:.55rem 0 0; font-size:.94rem; }
        .section-kicker { color:#ff7772; font-family:'DM Mono',monospace; text-transform:uppercase; letter-spacing:.14em; font-size:.68rem; margin:1.2rem 0 .35rem; }
        h2 { letter-spacing:-.035em; }
        [data-testid="stMetric"] { background:linear-gradient(145deg,#1b1c21,#17181c); border:1px solid #34353b; border-radius:12px; padding:1rem 1.1rem; min-height:112px; }
        [data-testid="stMetricLabel"] { color:#aaa9ad; font-size:.78rem; }
        [data-testid="stMetricValue"] { color:#f4f3f1; font-size:1.65rem; font-weight:700; }
        [data-testid="stMetricDelta"] { color:#aaa9ad; }
        div[data-testid="stAlert"] { border:1px solid #59423c; background:#261d1a; border-radius:10px; }
        div[data-testid="stDataFrame"] { border:1px solid #34353b; border-radius:10px; overflow:hidden; }
        .footnote { color:#96959b; font-size:.78rem; line-height:1.5; }
        .stCaption { color:#9e9da3; }
        </style>
        <div class="hero">
          <div class="eyebrow">Race Strategy Lab · 2024 / Round 01</div>
          <h1>Find the window.<br>Own the race.</h1>
          <p>Bahrain Grand Prix · strategy simulation and tyre-compound comparison</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="footnote">MODEL NOTE &nbsp; Strategy times are estimates. '
        'Pit loss and fuel effects are approximate; some plans extend beyond '
        'observed tyre ages.</div>',
        unsafe_allow_html=True,
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

    if not ACTUAL_COMPARISON_PATH.exists():
        st.warning(
            "The all-driver comparison has not been generated yet. Run "
            "scripts/compare_actual_result.py after cleaning the race data."
        )
    else:
        comparison = pd.read_csv(ACTUAL_COMPARISON_PATH)
        mae = comparison["absolute_error_seconds"].mean()
        rmse = (comparison["error_seconds"].pow(2).mean()) ** 0.5
        bias = comparison["error_seconds"].mean()
        winner_error = float(
            comparison.loc[
                comparison["driver_number"].eq(1), "error_seconds"
            ].iloc[0]
        )
        st.markdown('<div class="section-kicker">Reality check · Bahrain 2024</div>', unsafe_allow_html=True)
        st.subheader("Actual result vs. model replay · all 20 drivers")
        comparison_columns = st.columns(4)
        comparison_columns[0].metric(
            "Drivers compared",
            f"{len(comparison)}",
            help="Each driver's actual tyre sequence is replayed by a model fitted without that driver's laps.",
        )
        comparison_columns[1].metric(
            "Mean absolute error",
            f"{mae:.1f} s",
            help="Average absolute difference between model replay and official elapsed time.",
        )
        comparison_columns[2].metric(
            "Mean signed error",
            f"{bias:+.1f} s",
            help="Positive means the model tends to estimate slower race times.",
        )
        comparison_columns[3].metric("Winner replay error", f"{winner_error:+.1f} s")
        st.markdown(
            f"RMSE: **{rmse:.1f} s**. The chart compares each driver's official elapsed time "
            "with a model replay of that driver's observed compounds and pit laps."
        )
        scatter = alt.Chart(comparison).mark_circle(size=100, opacity=0.85).encode(
            x=alt.X("actual_time_seconds:Q", title="Official elapsed time (seconds)"),
            y=alt.Y("predicted_time_seconds:Q", title="Model replay time (seconds)"),
            color=alt.Color("actual_position:O", title="Actual finish position", scale=alt.Scale(scheme="redblue", reverse=True)),
            tooltip=[
                alt.Tooltip("actual_position:Q", title="Actual position"),
                alt.Tooltip("driver_name:N", title="Driver"),
                alt.Tooltip("actual_stint_compounds:N", title="Tyre sequence"),
                alt.Tooltip("actual_pit_laps_after:N", title="Pit after lap(s)"),
                alt.Tooltip("actual_time_official:N", title="Official time"),
                alt.Tooltip("predicted_time_seconds:Q", title="Model time (s)", format=".1f"),
                alt.Tooltip("error_seconds:Q", title="Model - actual (s)", format="+.1f"),
            ],
        )
        line_limits = [
            min(comparison["actual_time_seconds"].min(), comparison["predicted_time_seconds"].min()),
            max(comparison["actual_time_seconds"].max(), comparison["predicted_time_seconds"].max()),
        ]
        reference_line = alt.Chart(
            pd.DataFrame({"actual_time_seconds": line_limits, "predicted_time_seconds": line_limits})
        ).mark_line(color="#aaa9ad", strokeDash=[6, 4]).encode(
            x="actual_time_seconds:Q", y="predicted_time_seconds:Q"
        )
        chart = (reference_line + scatter).properties(height=340).interactive()
        st.altair_chart(chart, width="stretch")
        st.caption("The dashed diagonal marks a perfect time match. Points farther from it have larger replay errors.")

        comparison_table = comparison[
            [
                "actual_position",
                "driver_name",
                "actual_laps",
                "actual_stint_compounds",
                "actual_pit_laps_after",
                "actual_time_official",
                "predicted_time_seconds",
                "error_seconds",
            ]
        ].rename(
            columns={
                "actual_position": "Actual P",
                "driver_name": "Driver",
                "actual_laps": "Laps",
                "actual_stint_compounds": "Actual tyre sequence",
                "actual_pit_laps_after": "Pit after lap(s)",
                "actual_time_official": "Official time",
                "predicted_time_seconds": "Model replay (s)",
                "error_seconds": "Error (s)",
            }
        )
        st.dataframe(
            comparison_table,
            hide_index=True,
            width="stretch",
            column_config={
                "Model replay (s)": st.column_config.NumberColumn(format="%.3f"),
                "Error (s)": st.column_config.NumberColumn(format="%+.3f"),
            },
        )
        st.warning(
            "Retrospective driver holdout: each replay model excludes that driver's laps, "
            "but trains on the other drivers from this same Grand Prix. This is not a "
            "pre-race test on an unseen event. It uses approximate fuel and pit loss and "
            "does not model driver/car pace, traffic, or race incidents."
        )
        st.markdown(
            'Sources: [FIA final race classification](https://api.fia.com/sites/default/files/doc_32_-_2024_bahrain_grand_prix_-_final_race_classification.pdf) · '
            '[OpenF1 race data documentation](https://openf1.org/docs/)',
            unsafe_allow_html=False,
        )

    st.sidebar.markdown('<div class="eyebrow">Race controls</div>', unsafe_allow_html=True)
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

    st.markdown('<div class="section-kicker">At a glance</div>', unsafe_allow_html=True)
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

    st.markdown('<div class="section-kicker">Strategy analysis</div>', unsafe_allow_html=True)
    st.subheader("Estimated race time by first pit lap")
    chart = (
        alt.Chart(filtered)
        .mark_circle(size=82, opacity=0.78, stroke="#111216", strokeWidth=1)
        .encode(
            x=alt.X("first_pit_lap:Q", title="First pit after lap", axis=alt.Axis(tickMinStep=2)),
            y=alt.Y("predicted_race_time_seconds:Q", title="Estimated race time (seconds)", scale=alt.Scale(zero=False)),
            color=alt.Color("stint_compounds:N", title="Tyre sequence", scale=alt.Scale(range=["#e10600", "#f4f3f1", "#9fa3aa", "#ffb800"])),
            tooltip=[
                alt.Tooltip("first_pit_lap:Q", title="First pit lap"),
                alt.Tooltip("stint_compounds:N", title="Tyre sequence"),
                alt.Tooltip("stint_lengths:N", title="Stint lengths"),
                alt.Tooltip("predicted_race_time_seconds:Q", title="Estimated time (s)", format=".1f"),
                alt.Tooltip("laps_beyond_observed_tyre_age:Q", title="Laps beyond observed age"),
            ],
        )
        .properties(height=360, background="transparent")
        .configure_view(strokeOpacity=0)
        .configure_axis(labelColor="#b8b7bd", titleColor="#d8d7db", gridColor="#303137", domainColor="#55565c", tickColor="#55565c")
        .configure_legend(labelColor="#d8d7db", titleColor="#d8d7db", orient="top")
        .interactive()
    )
    st.altair_chart(chart, width="stretch")
    st.caption(
        "Lower points indicate a faster model estimate. Colour identifies "
        "the compound sequence; extrapolated plans are included unless filtered out."
    )

    st.markdown('<div class="section-kicker">Decision table</div>', unsafe_allow_html=True)
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
    display_table = filtered[visible_columns].head(30).rename(
        columns={
            "pit_stops": "Pit stops",
            "pit_laps_after": "Pit after lap(s)",
            "stint_compounds": "Tyre sequence",
            "stint_lengths": "Stint lengths (laps)",
            "predicted_race_time_seconds": "Estimated race time (s)",
            "pit_loss_seconds_each": "Pit loss / stop (s)",
            "laps_beyond_observed_tyre_age": "Unobserved-age laps",
            "within_observed_tyre_age": "Within observed ages",
        }
    )
    st.dataframe(
        display_table,
        hide_index=True,
        width="stretch",
        column_config={
            "Estimated race time (s)": st.column_config.NumberColumn(format="%.1f"),
            "Pit loss / stop (s)": st.column_config.NumberColumn(format="%.1f"),
            "Within observed ages": st.column_config.CheckboxColumn(),
        },
    )
    st.caption(
        f"Showing the fastest 30 of {len(filtered):,} matching plans. "
        "Race-time values are estimates, not measured race outcomes."
    )


if __name__ == "__main__":
    main()

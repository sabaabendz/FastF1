"""Inspect lap, tyre-stint, and pit-stop fields for the sample race."""

from pathlib import Path

import pandas as pd

from load_race_session import CACHE_DIR, load_race_session


STINT_COLUMNS = [
    "driver_number",
    "stint_number",
    "lap_start",
    "lap_end",
    "compound",
    "tyre_age_at_start",
]


def add_tyre_info_to_laps(
    laps: pd.DataFrame,
    stints: pd.DataFrame,
    pit_stops: pd.DataFrame,
) -> pd.DataFrame:
    """Match each lap to its driver's stint and mark pit-stop laps."""
    # A driver may have several stints, so first make lap/stint candidates.
    candidates = laps.merge(
        stints[STINT_COLUMNS],
        on="driver_number",
        how="left",
    )

    # Keep only the stint whose lap range contains this lap number.
    in_stint = candidates["lap_number"].ge(candidates["lap_start"]) & (
        candidates["lap_number"].le(candidates["lap_end"])
    )
    laps_with_stints = candidates.loc[in_stint].copy()

    # Age increases by one for each lap after the stint's starting lap.
    laps_with_stints["tyre_age"] = (
        laps_with_stints["tyre_age_at_start"]
        + laps_with_stints["lap_number"]
        - laps_with_stints["lap_start"]
    )

    pit_lap_keys = pit_stops[["driver_number", "lap_number"]].drop_duplicates()
    pit_lap_keys["is_pit_stop_lap"] = True
    result = laps_with_stints.merge(
        pit_lap_keys,
        on=["driver_number", "lap_number"],
        how="left",
    )
    result["is_pit_stop_lap"] = result["is_pit_stop_lap"].notna()
    return result


def main() -> None:
    race = load_race_session(
        year=2024,
        country_name="Bahrain",
        session_name="Race",
        cache_dir=CACHE_DIR,
    )
    laps = add_tyre_info_to_laps(race.laps, race.stints, race.pit_stops)

    print("Lap timing fields:")
    print("lap_number, lap_duration, is_pit_out_lap")
    print("Tyre fields are in the stints table:")
    print(", ".join(STINT_COLUMNS))
    print("\nSample laps for driver 1 (Verstappen):")
    sample_columns = [
        "driver_number",
        "lap_number",
        "lap_duration",
        "compound",
        "tyre_age",
        "is_pit_stop_lap",
        "is_pit_out_lap",
    ]
    print(
        laps.loc[laps["driver_number"].eq(1), sample_columns]
        .head(8)
        .to_string(index=False)
    )

    first_stop = race.pit_stops.loc[
        race.pit_stops["driver_number"].eq(1)
    ].iloc[0]
    stop_lap = int(first_stop["lap_number"])
    pit_lap_example = laps.loc[
        laps["driver_number"].eq(1)
        & laps["lap_number"].between(stop_lap, stop_lap + 1),
        sample_columns,
    ]
    print(f"\nDriver 1 pit stop: lap {stop_lap}")
    print(pit_lap_example.to_string(index=False))
    print(f"\nMatched laps: {len(laps)} of {len(race.laps)}")


if __name__ == "__main__":
    main()


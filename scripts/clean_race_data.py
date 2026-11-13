"""Flag pit, safety-car, yellow-flag, and wet laps for review."""

import os
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg
from dotenv import load_dotenv

from explore_race_data import add_tyre_info_to_laps
from load_race_session import RaceSessionData


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_cleaning_audit.csv"
SESSION_KEY = 9472
FUEL_BURN_KG_PER_LAP = 1.7
FUEL_EFFECT_SECONDS_PER_KG = 0.03


def read_frame(
    connection: psycopg.Connection,
    query: str,
    session_key: int,
) -> pd.DataFrame:
    """Run one parameterized query and return its rows as a DataFrame."""
    with connection.cursor() as cursor:
        cursor.execute(query, (session_key,))
        rows = cursor.fetchall()
        columns = [column.name for column in cursor.description]
    return pd.DataFrame.from_records(rows, columns=columns)


def load_race_from_postgres(database_url: str, session_key: int) -> RaceSessionData:
    """Read the raw race tables from PostgreSQL for the cleaning step."""
    with psycopg.connect(database_url) as connection:
        session_rows = read_frame(
            connection,
            "SELECT * FROM race_sessions WHERE session_key = %s",
            session_key,
        )
        if session_rows.empty:
            raise ValueError(f"Session {session_key} is not stored in PostgreSQL.")

        laps = read_frame(
            connection,
            """
            SELECT driver_number, lap_number, date_start, lap_duration,
                   duration_sector_1, duration_sector_2, duration_sector_3,
                   is_pit_out_lap
            FROM laps WHERE session_key = %s
            """,
            session_key,
        )
        stints = read_frame(
            connection,
            """
            SELECT driver_number, stint_number, lap_start, lap_end,
                   compound, tyre_age_at_start
            FROM stints WHERE session_key = %s
            """,
            session_key,
        )
        pit_stops = read_frame(
            connection,
            """
            SELECT driver_number, lap_number, lane_duration,
                   stop_duration, pit_duration
            FROM pit_stops WHERE session_key = %s
            """,
            session_key,
        )
        weather = read_frame(
            connection,
            """
            SELECT observed_at AS date, rainfall
            FROM weather_observations WHERE session_key = %s
            """,
            session_key,
        )
        race_control = read_frame(
            connection,
            """
            SELECT observed_at AS date, category, message, lap_number, flag
            FROM race_control_messages WHERE session_key = %s
            """,
            session_key,
        )

    return RaceSessionData(
        session_info=session_rows.iloc[0].to_dict(),
        laps=laps,
        stints=stints,
        pit_stops=pit_stops,
        weather=weather,
        race_control=race_control,
    )


def safety_car_lap_numbers(
    race_control: pd.DataFrame,
    final_lap: int,
) -> set[int]:
    """Expand Safety Car and Virtual Safety Car messages into lap ranges."""
    if race_control.empty:
        return set()

    messages = race_control.loc[
        race_control["category"].eq("SafetyCar")
        | race_control["message"].str.contains(
            "SAFETY CAR|VIRTUAL SAFETY CAR|\\bVSC\\b",
            case=False,
            na=False,
            regex=True,
        )
    ].copy()
    messages["event_time"] = pd.to_datetime(messages["date"], utc=True)
    messages = messages.sort_values("event_time")

    intervals: list[tuple[int, int]] = []
    active_start: int | None = None
    for _, event in messages.iterrows():
        if pd.isna(event["lap_number"]):
            continue

        lap = int(event["lap_number"])
        message = str(event["message"]).upper()
        deployment = "DEPLOY" in message or "DEPLOYMENT" in message
        ending = any(
            phrase in message
            for phrase in ("IN THIS LAP", "ENDING", "WITHDRAWN", "ENDED")
        )

        if deployment:
            if active_start is not None:
                intervals.append((active_start, max(active_start, lap - 1)))
            active_start = lap
        elif ending:
            if active_start is None:
                intervals.append((lap, lap))
            else:
                intervals.append((active_start, max(active_start, lap)))
                active_start = None

    if active_start is not None:
        intervals.append((active_start, final_lap))

    return {
        lap
        for first_lap, last_lap in intervals
        for lap in range(first_lap, last_lap + 1)
    }


def add_cleaning_flags(
    laps: pd.DataFrame,
    weather: pd.DataFrame,
    race_control: pd.DataFrame,
) -> pd.DataFrame:
    """Add auditable condition flags without deleting any raw lap rows."""
    result = laps.copy()
    result["is_inlap"] = result["is_pit_stop_lap"].fillna(False).astype(bool)
    result["is_outlap"] = result["is_pit_out_lap"].fillna(False).astype(bool)
    result["is_race_start_lap"] = result["lap_number"].eq(1)

    max_lap = int(result["lap_number"].max())
    safety_car_laps = safety_car_lap_numbers(race_control, max_lap)
    result["is_safety_car_lap"] = result["lap_number"].isin(safety_car_laps)

    yellow_laps: set[int] = set()
    if not race_control.empty:
        yellow_events = race_control.loc[
            race_control["category"].eq("Flag")
            & race_control["flag"].fillna("").str.contains(
                "YELLOW",
                case=False,
            )
        ]
        yellow_laps = {
            int(lap)
            for lap in yellow_events["lap_number"].dropna().unique()
        }
    result["is_yellow_flag_lap"] = result["lap_number"].isin(yellow_laps)

    weather_for_join = weather[["date", "rainfall"]].dropna(subset=["date"]).copy()
    weather_for_join["weather_time"] = pd.to_datetime(
        weather_for_join.pop("date"),
        utc=True,
    )
    result["lap_start_time"] = pd.to_datetime(result["date_start"], utc=True)
    result = pd.merge_asof(
        result.sort_values("lap_start_time"),
        weather_for_join.sort_values("weather_time"),
        left_on="lap_start_time",
        right_on="weather_time",
        direction="backward",
        tolerance=timedelta(seconds=90),
    )
    result["weather_matched"] = result["weather_time"].notna()
    result["is_wet_lap"] = result["rainfall"].fillna(False).astype(bool)

    required_values = result[["lap_duration", "compound", "tyre_age"]].notna().all(axis=1)
    result["keep_for_degradation_model"] = (
        required_values
        & ~result["is_inlap"]
        & ~result["is_outlap"]
        & ~result["is_race_start_lap"]
        & ~result["is_safety_car_lap"]
        & ~result["is_wet_lap"]
        & result["weather_matched"]
    )
    return result.sort_values(["driver_number", "lap_number"]).reset_index(drop=True)


def add_fuel_correction(
    laps: pd.DataFrame,
    race_lap_count: int,
    fuel_burn_kg_per_lap: float = FUEL_BURN_KG_PER_LAP,
    seconds_per_kg: float = FUEL_EFFECT_SECONDS_PER_KG,
) -> pd.DataFrame:
    """Estimate a common low-fuel reference time using a linear fuel model.

    Fuel load is not measured in this dataset, so the two parameters are
    explicit assumptions and should be varied in sensitivity analysis.
    """
    result = laps.copy()
    laps_remaining_including_current = (
        race_lap_count - result["lap_number"] + 1
    ).clip(lower=0)
    result["estimated_fuel_kg_at_lap_start"] = (
        laps_remaining_including_current * fuel_burn_kg_per_lap
    )
    result["estimated_fuel_penalty_seconds"] = (
        result["estimated_fuel_kg_at_lap_start"] * seconds_per_kg
    )
    result["fuel_corrected_lap_time"] = (
        result["lap_duration"] - result["estimated_fuel_penalty_seconds"]
    )
    return result


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing; set it in the project .env file.")

    race = load_race_from_postgres(database_url, SESSION_KEY)
    laps_with_tyres = add_tyre_info_to_laps(race.laps, race.stints, race.pit_stops)
    audited_laps = add_cleaning_flags(
        laps_with_tyres,
        race.weather,
        race.race_control,
    )
    race_lap_count = int(audited_laps["lap_number"].max())
    audited_laps = add_fuel_correction(audited_laps, race_lap_count)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audited_laps.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved lap-level cleaning audit: {OUTPUT_PATH}")
    print(f"Lap records: {len(audited_laps)}")
    print(f"Inlap records: {int(audited_laps['is_inlap'].sum())}")
    print(f"Outlap records: {int(audited_laps['is_outlap'].sum())}")
    print(f"Race-start records: {int(audited_laps['is_race_start_lap'].sum())}")
    print(f"Safety Car / VSC records: {int(audited_laps['is_safety_car_lap'].sum())}")
    print(f"Yellow-flag records (marked, not removed): {int(audited_laps['is_yellow_flag_lap'].sum())}")
    print(f"Wet records: {int(audited_laps['is_wet_lap'].sum())}")
    print(f"Unmatched weather records: {int((~audited_laps['weather_matched']).sum())}")
    print(
        "Model-eligible records with estimated fuel correction: "
        f"{int(audited_laps['keep_for_degradation_model'].sum())}"
    )
    print(
        "Estimated time gain per lap of fuel burned: "
        f"{FUEL_BURN_KG_PER_LAP * FUEL_EFFECT_SECONDS_PER_KG:.3f} seconds"
    )


if __name__ == "__main__":
    main()

"""Load the cached OpenF1 race data into the local PostgreSQL database."""

import os
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg
from dotenv import load_dotenv

from load_race_session import CACHE_DIR, load_race_session


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"

SESSION_COLUMNS = [
    "session_key",
    "meeting_key",
    "year",
    "country_name",
    "location",
    "session_name",
    "session_type",
    "circuit_short_name",
    "date_start",
    "date_end",
    "is_cancelled",
]
LAP_COLUMNS = [
    "driver_number",
    "lap_number",
    "date_start",
    "lap_duration",
    "duration_sector_1",
    "duration_sector_2",
    "duration_sector_3",
    "i1_speed",
    "i2_speed",
    "st_speed",
    "is_pit_out_lap",
]
STINT_COLUMNS = [
    "driver_number",
    "stint_number",
    "lap_start",
    "lap_end",
    "compound",
    "tyre_age_at_start",
]
PIT_STOP_COLUMNS = [
    "driver_number",
    "lap_number",
    "date",
    "lane_duration",
    "stop_duration",
    "pit_duration",
]
WEATHER_COLUMNS = [
    "date",
    "air_temperature",
    "pressure",
    "humidity",
    "wind_direction",
    "rainfall",
    "wind_speed",
    "track_temperature",
]
RACE_CONTROL_COLUMNS = [
    "date",
    "category",
    "message",
    "driver_number",
    "lap_number",
    "flag",
    "scope",
    "sector",
    "qualifying_phase",
]


def database_value(value: Any) -> Any:
    """Convert pandas missing and NumPy values to values psycopg can store."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def dataframe_rows(frame: pd.DataFrame, columns: list[str]) -> list[tuple[Any, ...]]:
    """Return selected DataFrame columns as database-ready row tuples."""
    return [
        tuple(database_value(value) for value in row)
        for row in frame[columns].itertuples(index=False, name=None)
    ]


def load_race_into_postgres(database_url: str) -> None:
    """Create the schema and insert or refresh this race's records."""
    race = load_race_session(
        year=2024,
        country_name="Bahrain",
        session_name="Race",
        cache_dir=CACHE_DIR,
    )
    session = race.session_info
    session_row = tuple(session.get(column) for column in SESSION_COLUMNS)
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8-sig")

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema_sql)
            cursor.execute(
                """
                INSERT INTO race_sessions (
                    session_key, meeting_key, year, country_name, location,
                    session_name, session_type, circuit_short_name,
                    date_start, date_end, is_cancelled
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_key) DO UPDATE SET
                    meeting_key = EXCLUDED.meeting_key,
                    year = EXCLUDED.year,
                    country_name = EXCLUDED.country_name,
                    location = EXCLUDED.location,
                    session_name = EXCLUDED.session_name,
                    session_type = EXCLUDED.session_type,
                    circuit_short_name = EXCLUDED.circuit_short_name,
                    date_start = EXCLUDED.date_start,
                    date_end = EXCLUDED.date_end,
                    is_cancelled = EXCLUDED.is_cancelled
                """,
                session_row,
            )

            session_key = int(session["session_key"])
            driver_numbers = set()
            for frame in (race.laps, race.stints, race.pit_stops):
                driver_numbers.update(
                    int(number)
                    for number in frame["driver_number"].dropna().unique()
                )
            driver_rows = [(session_key, number) for number in driver_numbers]
            cursor.executemany(
                """
                INSERT INTO drivers (session_key, driver_number)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                driver_rows,
            )

            lap_rows = [
                (session_key, *row)
                for row in dataframe_rows(race.laps, LAP_COLUMNS)
            ]
            cursor.executemany(
                """
                INSERT INTO laps (
                    session_key, driver_number, lap_number, date_start,
                    lap_duration, duration_sector_1, duration_sector_2,
                    duration_sector_3, i1_speed, i2_speed, st_speed,
                    is_pit_out_lap
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_key, driver_number, lap_number) DO UPDATE SET
                    date_start = EXCLUDED.date_start,
                    lap_duration = EXCLUDED.lap_duration,
                    duration_sector_1 = EXCLUDED.duration_sector_1,
                    duration_sector_2 = EXCLUDED.duration_sector_2,
                    duration_sector_3 = EXCLUDED.duration_sector_3,
                    i1_speed = EXCLUDED.i1_speed,
                    i2_speed = EXCLUDED.i2_speed,
                    st_speed = EXCLUDED.st_speed,
                    is_pit_out_lap = EXCLUDED.is_pit_out_lap
                """,
                lap_rows,
            )

            stint_rows = [
                (session_key, *row)
                for row in dataframe_rows(race.stints, STINT_COLUMNS)
            ]
            cursor.executemany(
                """
                INSERT INTO stints (
                    session_key, driver_number, stint_number, lap_start,
                    lap_end, compound, tyre_age_at_start
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_key, driver_number, stint_number) DO UPDATE SET
                    lap_start = EXCLUDED.lap_start,
                    lap_end = EXCLUDED.lap_end,
                    compound = EXCLUDED.compound,
                    tyre_age_at_start = EXCLUDED.tyre_age_at_start
                """,
                stint_rows,
            )

            pit_stop_rows = [
                (
                    session_key,
                    *row[:2],
                    row[2],
                    *row[3:],
                )
                for row in dataframe_rows(race.pit_stops, PIT_STOP_COLUMNS)
            ]
            cursor.executemany(
                """
                INSERT INTO pit_stops (
                    session_key, driver_number, lap_number, stop_date,
                    lane_duration, stop_duration, pit_duration
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_key, driver_number, lap_number) DO UPDATE SET
                    stop_date = EXCLUDED.stop_date,
                    lane_duration = EXCLUDED.lane_duration,
                    stop_duration = EXCLUDED.stop_duration,
                    pit_duration = EXCLUDED.pit_duration
                """,
                pit_stop_rows,
            )

            weather_rows = []
            for row in dataframe_rows(race.weather, WEATHER_COLUMNS):
                rainfall = None if row[5] is None else bool(row[5])
                weather_rows.append((session_key, *row[:5], rainfall, *row[6:]))
            cursor.executemany(
                """
                INSERT INTO weather_observations (
                    session_key, observed_at, air_temperature, pressure,
                    humidity, wind_direction, rainfall, wind_speed,
                    track_temperature
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_key, observed_at) DO UPDATE SET
                    air_temperature = EXCLUDED.air_temperature,
                    pressure = EXCLUDED.pressure,
                    humidity = EXCLUDED.humidity,
                    wind_direction = EXCLUDED.wind_direction,
                    rainfall = EXCLUDED.rainfall,
                    wind_speed = EXCLUDED.wind_speed,
                    track_temperature = EXCLUDED.track_temperature
                """,
                weather_rows,
            )

            race_control_rows = [
                (session_key, *row)
                for row in dataframe_rows(race.race_control, RACE_CONTROL_COLUMNS)
            ]
            cursor.executemany(
                """
                INSERT INTO race_control_messages (
                    session_key, observed_at, category, message,
                    driver_number, lap_number, flag, scope, sector,
                    qualifying_phase
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_key, observed_at, category, message)
                DO UPDATE SET
                    driver_number = EXCLUDED.driver_number,
                    lap_number = EXCLUDED.lap_number,
                    flag = EXCLUDED.flag,
                    scope = EXCLUDED.scope,
                    sector = EXCLUDED.sector,
                    qualifying_phase = EXCLUDED.qualifying_phase
                """,
                race_control_rows,
            )

    print(f"Loaded session {session_key} into PostgreSQL.")
    print(f"Drivers: {len(driver_numbers)}")
    print(f"Lap records: {len(lap_rows)}")
    print(f"Stints: {len(stint_rows)}")
    print(f"Pit stops: {len(pit_stop_rows)}")
    print(f"Weather readings: {len(weather_rows)}")
    print(f"Race-control messages: {len(race_control_rows)}")


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing. Copy .env.example to .env and set "
            "the local PostgreSQL password."
        )
    load_race_into_postgres(database_url)


if __name__ == "__main__":
    main()


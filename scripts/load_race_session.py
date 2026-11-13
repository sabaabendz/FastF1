"""Load a completed F1 race and cache its lap, stint, and pit-stop data."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
OPENF1_API = "https://api.openf1.org/v1"


@dataclass
class RaceSessionData:
    """Related data tables for one race session."""

    session_info: dict[str, Any]
    laps: pd.DataFrame
    stints: pd.DataFrame
    pit_stops: pd.DataFrame
    weather: pd.DataFrame
    race_control: pd.DataFrame


def fetch_json(
    endpoint: str,
    params: dict[str, str | int],
    cache_dir: Path,
) -> Any:
    """Get one OpenF1 endpoint, reusing its saved JSON response when available."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key = json.dumps(params, sort_keys=True)
    cache_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()[:12]
    cache_path = cache_dir / f"{endpoint}_{cache_hash}.json"

    # Reuse the saved API response so reruns are faster and gentler on the API.
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    response = requests.get(
        f"{OPENF1_API}/{endpoint}",
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    cache_path.write_text(json.dumps(data), encoding="utf-8")
    return data


def load_race_session(
    year: int,
    country_name: str,
    session_name: str,
    cache_dir: Path,
) -> RaceSessionData:
    """Load the session details, lap times, tyre stints, and pit stops."""
    matching_sessions = fetch_json(
        "sessions",
        {
            "year": year,
            "country_name": country_name,
            "session_name": session_name,
        },
        cache_dir,
    )
    if not matching_sessions:
        raise ValueError(
            f"No {session_name} session found for {country_name} in {year}."
        )

    session_info = matching_sessions[0]
    session_key = session_info["session_key"]

    # OpenF1 uses the session key to connect all three tables to this race.
    laps = fetch_json("laps", {"session_key": session_key}, cache_dir)
    stints = fetch_json("stints", {"session_key": session_key}, cache_dir)
    pit_stops = fetch_json("pit", {"session_key": session_key}, cache_dir)
    weather = fetch_json("weather", {"session_key": session_key}, cache_dir)
    race_control = fetch_json(
        "race_control",
        {"session_key": session_key},
        cache_dir,
    )

    return RaceSessionData(
        session_info=session_info,
        laps=pd.DataFrame.from_records(laps),
        stints=pd.DataFrame.from_records(stints),
        pit_stops=pd.DataFrame.from_records(pit_stops),
        weather=pd.DataFrame.from_records(weather),
        race_control=pd.DataFrame.from_records(race_control),
    )


def main() -> None:
    race = load_race_session(
        year=2024,
        country_name="Bahrain",
        session_name="Race",
        cache_dir=CACHE_DIR,
    )

    print(f"Event: {race.session_info['country_name']}")
    print(f"Session: {race.session_info['session_name']}")
    print(f"Session key: {race.session_info['session_key']}")
    print(f"Lap records: {len(race.laps)}")
    print(f"Tyre stints: {len(race.stints)}")
    print(f"Pit stops: {len(race.pit_stops)}")
    print(f"Weather readings: {len(race.weather)}")
    print(f"Race-control messages: {len(race.race_control)}")
    print(f"Cache directory: {CACHE_DIR}")


if __name__ == "__main__":
    main()


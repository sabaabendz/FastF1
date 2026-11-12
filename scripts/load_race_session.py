"""Load a completed F1 race session and report its basic lap data."""

from pathlib import Path

import fastf1
from fastf1.core import Session
from fastf1.exceptions import DataNotLoadedError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_ROOT / "data" / "cache"


def load_race_session(
    year: int,
    event: str,
    session_type: str,
    cache_dir: Path,
) -> Session:
    """Load one session's lap data, storing downloaded data in a local cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.configure(cache_dir=str(cache_dir))

    session = fastf1.get_session(year, event, session_type)
    session.load(
        laps=True,
        telemetry=False,
        weather=False,
        messages=False,
    )
    try:
        laps = session.laps
    except DataNotLoadedError as error:
        raise RuntimeError(
            "FastF1 did not return lap data. Since October 2026, archived "
            "F1 timing data requires an F1 TV Access, Pro, or Premium account. "
            "Authenticate with FastF1 and run this script again."
        ) from error
    if laps.empty:
        raise RuntimeError("FastF1 loaded the session but returned no laps.")
    return session


def main() -> None:
    session = load_race_session(
        year=2024,
        event="Bahrain",
        session_type="R",
        cache_dir=CACHE_DIR,
    )

    print(f"Event: {session.event['EventName']}")
    print(f"Session: {session.name}")
    print(f"Laps loaded: {len(session.laps)}")
    print(f"Drivers: {session.laps['Driver'].nunique()}")
    print(f"Cache directory: {CACHE_DIR}")


if __name__ == "__main__":
    main()

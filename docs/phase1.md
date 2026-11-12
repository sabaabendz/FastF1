# Phase 1: Setup and data exploration

## Goal

Prepare a reproducible Python project, load one completed F1 session, inspect its lap and tyre-stint data, and visualize lap time against tyre age for a few drivers.

## Project layout

- `src/f1_strategy/`: reusable project code.
- `scripts/`: runnable exploration scripts.
- `data/cache/`: cached API responses, excluded from Git.
- `data/raw/`: optional downloaded source data, excluded from Git.
- `docs/`: project decisions and learning notes.

## Setup decisions

- Use a Python virtual environment (`.venv`) so packages for this project do not affect other Python projects.
- Use OpenF1's historical HTTP API through Requests for session, lap, tyre-stint, and pit-stop records. Its historical data is free without authentication from 2023 onward. OpenF1 is an unofficial, community-run source.
- Keep the Phase 1 libraries in `requirements.txt`: Requests for API calls, pandas for data tables, and Matplotlib for plots.
- Pin dependency versions so setup is consistent across machines.
- Ignore generated data and the virtual environment because they are reproducible or machine-specific and should not be committed.
- Use a completed race session for exploration, so its laps and pit stops are available.

## Task 2: Load one race session

Runnable script: `scripts/load_race_session.py`.

It loads the 2024 Bahrain Grand Prix Race session from OpenF1: session metadata, laps, tyre stints, and pit stops. OpenF1 gives each session a numeric key; the loader uses that key to request the matching records from each endpoint. Responses are cached as JSON in `data/cache/`, so reruns do not need to download the same records again.

Run it from the project root with the virtual environment active:

```powershell
python scripts/load_race_session.py
```

The first run requires internet access and prints the session, record counts, and cache directory. Later runs reuse the cached responses.

## Why we changed source

Formula 1 began requiring an F1 TV Access, Pro, or Premium account for archived live-timing data in October 2026, which prevents FastF1 from downloading laps without a subscription. Since we do not have that account, we switched this learning project to OpenF1's free historical API. We verified that its Bahrain 2024 endpoints return lap, stint, and pit-stop records. OpenF1 is unofficial, so that provenance is a project limitation to include when discussing the data.

## Domain concepts to inspect

A **compound** is the tyre type (for example, Soft, Medium, or Hard). A **stint** is a continuous run on one set of tyres. **Tyre age** is the number of laps that set has been used. The pit entry and pit exit laps often have unusual timing, and the first lap after a stop is an outlap; these need to be recognized before training a pace model.

## Data-science caveat

A lap-time-versus-tyre-age chart is descriptive, not proof that tyre age caused the observed change. Fuel load decreases during a race, while traffic, weather, track evolution, driver pace, and Safety Car periods also affect lap time. Later cleaning and modeling phases will handle some of these effects explicitly.

## Task 3: Explore laps, tyre stints, and pit laps

Runnable script: `scripts/explore_race_data.py`.

OpenF1 stores timing and tyre information in separate tables. The `laps` table provides `lap_number`, `lap_duration` (seconds), and `is_pit_out_lap`. The `stints` table provides `compound`, `lap_start`, `lap_end`, and `tyre_age_at_start`. The script joins these by driver and checks that each lap falls inside the stint's lap range. It calculates lap tyre age as `tyre_age_at_start + lap_number - lap_start`.

The `pit` table reports `driver_number`, `lap_number`, and `pit_duration`. The script marks those driver/lap pairs as pit-stop laps, then displays a stop lap and the following lap so the outlap flag is visible beside its timing. In the Bahrain example, Verstappen's pit record is on lap 17 and lap 18 is flagged as an outlap. That outlap took 117.854 seconds, much longer than his surrounding racing laps, showing why pit-related laps need special treatment before fitting a tyre-pace model.

Run it from the project root:

```powershell
python scripts/explore_race_data.py
```

The join matched all 1,129 available lap records to exactly one tyre stint in this race. This is a check for this session, not a guarantee that every race's source data will be complete or perfectly aligned.

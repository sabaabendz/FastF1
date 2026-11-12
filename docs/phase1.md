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

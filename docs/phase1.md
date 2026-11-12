# Phase 1: Setup and data exploration

## Goal

Prepare a reproducible Python project, load one completed F1 session through FastF1, inspect its lap and tyre-stint data, and visualize lap time against tyre age for a few drivers.

## Project layout

- `src/f1_strategy/`: reusable project code.
- `scripts/`: runnable exploration scripts.
- `data/cache/`: local FastF1 cache, excluded from Git.
- `data/raw/`: optional downloaded source data, excluded from Git.
- `docs/`: project decisions and learning notes.

## Setup decisions

- Use a Python virtual environment (`.venv`) so packages for this project do not affect other Python projects.
- Keep only the libraries needed for Phase 1 in `requirements.txt`: FastF1 for timing and telemetry data, pandas for its table-like lap data, and Matplotlib for plots.
- Ignore generated data and the virtual environment because they are reproducible or machine-specific and should not be committed.
- Use a completed race session for exploration, so its laps and pit stops are available. We will record the selected event and season in the exploration script once we load it.

## Domain concepts to inspect

A **compound** is the tyre type (for example, Soft, Medium, or Hard). A **stint** is a continuous run on one set of tyres. **Tyre life** is the number of laps that set has been used. The pit entry and pit exit laps often have unusual timing, and the first lap after a stop is an outlap; these need to be recognized before training a pace model.

## Data-science caveat

A lap-time-versus-tyre-age chart is descriptive, not proof that tyre age caused the observed change. Fuel load decreases during a race, while traffic, weather, track evolution, driver pace, and Safety Car periods also affect lap time. Later cleaning and modeling phases will handle some of these effects explicitly.

## Task 2: Load one race session

Runnable script: `scripts/load_race_session.py`.

It loads the 2024 Bahrain Grand Prix Race session and asks FastF1 to load laps while skipping telemetry, weather, and race-control messages. This is enough for the lap and tyre exploration planned next and avoids downloading data we do not use yet. The FastF1 cache lives in `data/cache/`, which is ignored by Git.

Run it from the project root with the virtual environment active:

```powershell
python scripts/load_race_session.py
```

The script prints the event, session name, lap-row count, and number of drivers. The first run requires internet access and can take longer while FastF1 downloads and parses data; later runs can reuse cached data.

### Access requirement discovered

Formula 1 began requiring authentication to access archived live-timing data in October 2026. FastF1 can still resolve the event schedule without an account, but lap timing requires an active F1 TV Access, Pro, or Premium account. The loader checks for an empty lap table so this limitation appears as a clear error instead of a later, confusing failure. Never commit account credentials; use FastF1's supported authentication flow locally.

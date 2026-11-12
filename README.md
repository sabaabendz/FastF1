# F1 Race Strategy Engine

A portfolio project that will estimate tyre degradation and simulate pit strategies to find a fast race plan.

## Current phase

Phase 1 — setup and exploration. See [docs/phase1.md](docs/phase1.md) for scope and decisions.

## Data source

This project uses OpenF1 for historical F1 data. Its historical API provides sessions, lap times, tyre stints, and pit-stop information for 2023 onward without authentication. OpenF1 is an unofficial, community-run data source.

## Setup

Requires Python 3.11 or newer. From the project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The current dependencies are Requests for HTTP calls, pandas for table-like lap data, and Matplotlib for plots. Later phases will add their own dependencies when we reach them.

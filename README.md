# F1 Race Strategy Engine

A portfolio project that will estimate tyre degradation and simulate pit strategies to find a fast race plan.

## Current phase

Phase 6 — dashboard and Docker packaging. See [docs/phase1.md](docs/phase1.md) through [docs/phase5.md](docs/phase5.md) for the data pipeline and model decisions, and [docs/phase6.md](docs/phase6.md) for running the dashboard and containers.

## Data source

This project uses OpenF1 for historical F1 data. Its historical API provides sessions, lap times, tyre stints, and pit-stop information for 2023 onward without authentication. OpenF1 is an unofficial, community-run data source.

## Setup

Requires Python 3.11 or newer and Docker Desktop with its Linux engine running. From the project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Change `POSTGRES_PASSWORD` and the password in `DATABASE_URL` in your local `.env` to the same value. `.env` is ignored by Git.

Start PostgreSQL and load the sample race:

```powershell
docker compose up -d postgres
python scripts/load_to_postgres.py
```

Generate the cleaning audit and strategy ranking, then start the dashboard locally:

```powershell
python scripts/clean_race_data.py
python scripts/simulate_pit_strategy.py
python -m streamlit run src/f1_strategy/dashboard.py
```

The dashboard opens at `http://localhost:8501`. See [docs/phase6.md](docs/phase6.md) for the container workflow.


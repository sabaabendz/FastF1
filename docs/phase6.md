# Phase 6: Dashboard and Docker

## Streamlit dashboard

The dashboard reads the generated strategy ranking from `reports/bahrain_2024_strategy_results.csv`. It does not fit models or run the simulator when the page refreshes. It provides:

- a selector for one-stop or two-stop strategies;
- a filter for compound sequences;
- an optional filter to hide strategies that predict beyond tyre ages observed in the data;
- summary metrics, an estimated-time scatter chart, and a ranked table.

The interface uses a dark motorsport-inspired visual theme, high-contrast strategy metrics, an interactive chart with hover details, and clearer table labels. These are presentation changes only; the strategy calculations are unchanged.

Run the data pipeline first, then launch Streamlit:

```powershell
python scripts/clean_race_data.py
python scripts/simulate_pit_strategy.py
python scripts/compare_actual_result.py
python -m streamlit run src/f1_strategy/dashboard.py
```

Open `http://localhost:8501`. If the generated strategy CSV is missing, the app displays the commands needed to create it.

Streamlit's `cache_data` decorator reuses the parsed CSV during UI interactions. The sidebar controls filter the existing rows in memory; they do not change the model or strategy calculations.

## Docker setup

`Dockerfile` creates the Python dashboard and pipeline image. `compose.yaml` runs PostgreSQL, the Streamlit dashboard, and an optional one-shot pipeline. Generated reports are mounted into the dashboard container read-only so the app cannot modify its input files.

First ensure `.env` exists and contains the PostgreSQL password. To build the image and run the data pipeline inside Docker:

```powershell
docker compose --profile pipeline run --build --rm pipeline
docker compose up --build -d dashboard
```

Compose starts PostgreSQL and waits for its health check. The pipeline service loads the sample race, creates the cleaning audit and strategy ranking, generates the real-race comparison, and stores OpenF1's response cache in a named Docker volume. The dashboard then serves at `http://localhost:8501`.

The pipeline container uses the internal database hostname `postgres`; the local `.env` keeps `localhost` for Python scripts run directly on Windows. This lets the same project support both workflows without editing the password into source files.

To stop the dashboard and database while preserving the PostgreSQL data and API cache:

```powershell
docker compose down
```

## Verification and limits

The dashboard was rendered locally with Streamlit's app runner without application errors, including the actual-race comparison, and its Docker image rebuilt successfully. The containerized dashboard returned HTTP 200, PostgreSQL passed its health check, and the optional pipeline Compose profile validated. The full data pipeline profile was not run in Docker during this step.

The dashboard presents the Phase 5 prototype's results and a retrospective comparison with the official Bahrain 2024 winner's time and strategy. It does not make the underlying assumptions more reliable. The model was trained on the same race, so this comparison is in-sample rather than an independent forecast. Fuel and pit loss remain estimates, and the model uses only one race. See [docs/actual_comparison.md](actual_comparison.md) for the result and validation limits. The dashboard currently supports the sample Bahrain race rather than arbitrary race selection.

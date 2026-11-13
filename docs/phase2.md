# Phase 2: PostgreSQL schema and data loading

## Goal

Store the OpenF1 race records in PostgreSQL so later cleaning, feature generation, and modeling use a repeatable database source instead of only local JSON files.

## Local database

`compose.yaml` starts a PostgreSQL 17 container with a named volume, so its database data survives container restarts. Copy `.env.example` to `.env`, choose a local password, and use the same password in `DATABASE_URL`. The `.env` file is ignored by Git; never commit it.

```powershell
Copy-Item .env.example .env
docker compose up -d postgres
```

The Compose health check waits for PostgreSQL to accept connections. The app connects through Psycopg 3 using `DATABASE_URL`; `python-dotenv` reads that setting from the local `.env` file.

## Schema design

The SQL lives in `sql/schema.sql`:

- `race_sessions` stores metadata once per session.
- `drivers` identifies drivers within a session. Driver numbers can change across seasons, so the key is `(session_key, driver_number)`.
- `laps` stores one row per driver per lap (a lap record), keyed by `(session_key, driver_number, lap_number)`.
- `stints` stores compound and tyre age at the beginning of each stint, keyed by `(session_key, driver_number, stint_number)`.
- `pit_stops` stores pit timing, keyed by `(session_key, driver_number, lap_number)`.

Foreign keys connect laps, stints, and stops to a known session driver. Primary keys prevent duplicate records when we rerun the loader. Check constraints reject invalid lap numbers, stint ranges, and tyre ages. Lap-level sector times and speed traps are stored because they may help later analysis; high-frequency car telemetry is not part of this phase.

## Loading the sample race

Run the loader from the project root:

```powershell
python scripts/load_to_postgres.py
```

The script reuses the cached OpenF1 JSON, creates the tables, and upserts the 2024 Bahrain Race session, drivers, laps, stints, and pit stops in one database transaction. Upsert means a repeated run refreshes matching rows instead of adding duplicates. The loader converts pandas and NumPy values to regular Python values and turns missing values into SQL `NULL`.

Verified in Docker Desktop with PostgreSQL 17: one session, 20 drivers, 1,129 lap records, 63 stints, and 43 pit stops. I ran the loader twice; the counts stayed the same, confirming that the upserts are idempotent. To stop the database container while keeping its data volume, run `docker compose down`.

## Why these choices

Psycopg 3 is the PostgreSQL adapter. Its binary extra includes the client library, so a separate PostgreSQL client install is not needed on the Python side. Raw SQL makes the relational schema, keys, and constraints visible for learning; an ORM can be considered later if the application grows.



CREATE TABLE IF NOT EXISTS race_sessions (
    session_key BIGINT PRIMARY KEY,
    meeting_key BIGINT NOT NULL,
    year SMALLINT NOT NULL CHECK (year >= 1950),
    country_name TEXT NOT NULL,
    location TEXT,
    session_name TEXT NOT NULL,
    session_type TEXT,
    circuit_short_name TEXT,
    date_start TIMESTAMPTZ,
    date_end TIMESTAMPTZ,
    is_cancelled BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS drivers (
    session_key BIGINT NOT NULL REFERENCES race_sessions (session_key) ON DELETE CASCADE,
    driver_number SMALLINT NOT NULL CHECK (driver_number > 0),
    PRIMARY KEY (session_key, driver_number)
);

CREATE TABLE IF NOT EXISTS laps (
    session_key BIGINT NOT NULL,
    driver_number SMALLINT NOT NULL,
    lap_number SMALLINT NOT NULL CHECK (lap_number > 0),
    date_start TIMESTAMPTZ,
    lap_duration DOUBLE PRECISION CHECK (lap_duration IS NULL OR lap_duration > 0),
    duration_sector_1 DOUBLE PRECISION,
    duration_sector_2 DOUBLE PRECISION,
    duration_sector_3 DOUBLE PRECISION,
    i1_speed DOUBLE PRECISION,
    i2_speed DOUBLE PRECISION,
    st_speed DOUBLE PRECISION,
    is_pit_out_lap BOOLEAN,
    PRIMARY KEY (session_key, driver_number, lap_number),
    FOREIGN KEY (session_key, driver_number)
        REFERENCES drivers (session_key, driver_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stints (
    session_key BIGINT NOT NULL,
    driver_number SMALLINT NOT NULL,
    stint_number SMALLINT NOT NULL CHECK (stint_number > 0),
    lap_start SMALLINT NOT NULL CHECK (lap_start > 0),
    lap_end SMALLINT NOT NULL CHECK (lap_end >= lap_start),
    compound TEXT NOT NULL,
    tyre_age_at_start SMALLINT NOT NULL CHECK (tyre_age_at_start >= 0),
    PRIMARY KEY (session_key, driver_number, stint_number),
    FOREIGN KEY (session_key, driver_number)
        REFERENCES drivers (session_key, driver_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pit_stops (
    session_key BIGINT NOT NULL,
    driver_number SMALLINT NOT NULL,
    lap_number SMALLINT NOT NULL CHECK (lap_number > 0),
    stop_date TIMESTAMPTZ,
    lane_duration DOUBLE PRECISION,
    stop_duration DOUBLE PRECISION,
    pit_duration DOUBLE PRECISION,
    PRIMARY KEY (session_key, driver_number, lap_number),
    FOREIGN KEY (session_key, driver_number)
        REFERENCES drivers (session_key, driver_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS weather_observations (
    session_key BIGINT NOT NULL REFERENCES race_sessions (session_key) ON DELETE CASCADE,
    observed_at TIMESTAMPTZ NOT NULL,
    air_temperature DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    wind_direction SMALLINT,
    rainfall BOOLEAN,
    wind_speed DOUBLE PRECISION,
    track_temperature DOUBLE PRECISION,
    PRIMARY KEY (session_key, observed_at)
);

CREATE TABLE IF NOT EXISTS race_control_messages (
    session_key BIGINT NOT NULL REFERENCES race_sessions (session_key) ON DELETE CASCADE,
    observed_at TIMESTAMPTZ NOT NULL,
    category TEXT NOT NULL,
    message TEXT NOT NULL,
    driver_number SMALLINT,
    lap_number SMALLINT,
    flag TEXT,
    scope TEXT,
    sector SMALLINT,
    qualifying_phase SMALLINT,
    PRIMARY KEY (session_key, observed_at, category, message)
);

CREATE INDEX IF NOT EXISTS idx_laps_session_lap
    ON laps (session_key, lap_number);
CREATE INDEX IF NOT EXISTS idx_stints_session_compound
    ON stints (session_key, compound);

# Phase 3: Cleaning and feature preparation

## Goal

Create a transparent lap-level audit that marks conditions which make a lap unsuitable for learning steady-state tyre degradation. Raw database records remain unchanged; the audit is a derived CSV so every inclusion or exclusion can be inspected.

## Current audit

Run from the project root after PostgreSQL is running and `.env` is configured:

```powershell
python scripts/clean_race_data.py
```

The script reads the raw laps, stints, pit stops, weather, and race-control data from PostgreSQL and writes `reports/bahrain_2024_cleaning_audit.csv` (the generated report is ignored by Git).

Verified for the 2024 Bahrain Race:

| Measure | Lap records |
| --- | ---: |
| Raw driver-lap records | 1,129 |
| Inlaps marked | 43 |
| Outlaps marked | 43 |
| Race-start laps marked | 20 |
| Safety Car / VSC laps | 0 |
| Yellow-flag laps marked and retained | 40 |
| Wet laps | 0 |
| Laps without matched weather | 0 |
| Eligible for degradation analysis before fuel correction | 1,024 |

These are driver-lap rows, not the number of laps in the Grand Prix. The event distance was 57 laps; 1,129 rows exist because each participating driver contributes a row for each lap they completed.

## Rules and rationale

- **Inlaps:** laps ending with a pit stop are excluded because drivers slow and enter the pit lane.
- **Outlaps:** laps after a pit stop are excluded because the tyres are cold and need to build temperature and grip.
- **Race-start laps:** retained in the audit but excluded from the steady-state degradation set. The standing start, traffic, and first-lap conditions make them unlike ordinary laps. This also avoids treating Hamilton's unusual first lap as ordinary tyre ageing.
- **Safety Car and VSC:** deployment/ending messages are expanded to affected lap ranges, then those laps are excluded because the field is constrained and tyre wear/lap time no longer represent normal racing. This Bahrain event had no such laps. A synthetic interval check verified the range expansion logic.
- **Wet conditions:** rainfall observations are matched to each lap using the latest reading at or before lap start, only when that reading is no more than 90 seconds old. A lap is wet when the matched observation reports rainfall. This race had no rainfall.
- **Yellow flags:** localized yellow-flag laps are marked but retained for now. Race control can describe only one sector or a brief hazard; excluding a whole lap may discard useful green-flag running. The flag marker allows later sensitivity checks.
- **Required data:** a row also needs lap duration, compound, and tyre age, supplied by joining each lap to its driver's stint range.

## Important limitation: fuel load

OpenF1 does not provide the car's fuel load per lap. Cars burn fuel as the race progresses, making them lighter and generally faster; this can hide some tyre-related lap-time loss. The 1,024 rows are therefore only eligible before fuel correction. Fuel correction remains the next task in Phase 3, and it will require a clearly labeled approximation rather than pretending we have measured fuel data.

## Data science cautions

Filtering is based on known race circumstances, but the rules are still assumptions. The audit preserves the flags so the effect of alternative rules can be compared later. A single race has a small sample and one set of conditions, so it cannot establish a general tyre-degradation relationship on its own.

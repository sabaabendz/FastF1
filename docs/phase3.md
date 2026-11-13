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
| Eligible for degradation analysis with estimated fuel correction | 1,024 |

These are driver-lap rows, not the number of laps in the Grand Prix. The event distance was 57 laps; 1,129 rows exist because each participating driver contributes a row for each lap they completed.

## Rules and rationale

- **Inlaps:** laps ending with a pit stop are excluded because drivers slow and enter the pit lane.
- **Outlaps:** laps after a pit stop are excluded because the tyres are cold and need to build temperature and grip.
- **Race-start laps:** retained in the audit but excluded from the steady-state degradation set. The standing start, traffic, and first-lap conditions make them unlike ordinary laps. This also avoids treating Hamilton's unusual first lap as ordinary tyre ageing.
- **Safety Car and VSC:** deployment/ending messages are expanded to affected lap ranges, then those laps are excluded because the field is constrained and tyre wear/lap time no longer represent normal racing. This Bahrain event had no such laps. A synthetic interval check verified the range expansion logic.
- **Wet conditions:** rainfall observations are matched to each lap using the latest reading at or before lap start, only when that reading is no more than 90 seconds old. A lap is wet when the matched observation reports rainfall. This race had no rainfall.
- **Yellow flags:** localized yellow-flag laps are marked but retained for now. Race control can describe only one sector or a brief hazard; excluding a whole lap may discard useful green-flag running. The flag marker allows later sensitivity checks.
- **Required data:** a row also needs lap duration, compound, and tyre age, supplied by joining each lap to its driver's stint range.

## Fuel correction: estimate, not measurement

OpenF1 does not provide the car's fuel load per lap. Fuel burns off during the race, making the car lighter and generally faster; this can hide some tyre-related lap-time loss. The script now adds three estimated columns while retaining the original `lap_duration`:

- `estimated_fuel_kg_at_lap_start`
- `estimated_fuel_penalty_seconds`
- `fuel_corrected_lap_time`

The simple linear model assumes 1.7 kg of fuel used per lap and a lap-time penalty of 0.03 seconds per kilogram. For lap `n` in a race of `N` laps:

```text
estimated fuel at lap start = (N - n + 1) × 1.7 kg
fuel penalty = estimated fuel × 0.03 seconds/kg
fuel-corrected lap time = observed lap time - fuel penalty
```

The 1.7 kg/lap value is a Bahrain reference estimate; fuel use varies by track, engine mode, traffic, and driver fuel saving. The 0.03 seconds/kg value is a commonly used central estimate in F1 strategy modeling; published analyses give a range around 0.02–0.04 seconds/kg. This correction moves early, heavier-fuel laps toward a common low-fuel reference. It does **not** recover the actual fuel load or prove the remaining lap-time change came from tyre wear.

For 57 laps, these assumptions estimate 96.9 kg at the beginning of lap 1 and 1.7 kg at the beginning of lap 57. The correction is about 2.91 seconds on lap 1 and 0.05 seconds on lap 57. That is a substantial shift, so later analysis should compare results under lower and higher assumptions rather than relying on only one setting.

## Data science cautions

Filtering and fuel correction use assumptions. The audit preserves raw lap times and all flags so alternative cleaning rules and fuel parameters can be compared later. Fuel estimate and race lap number are mechanically related in this model; the estimated fuel feature must not be mistaken for an independent measured signal. A single race has a small sample and one set of conditions, so it cannot establish a general tyre-degradation relationship on its own.

## References

- OpenF1 endpoint documentation (available lap, stint, and other session fields): [openf1.org/docs](https://openf1.org/docs/)
- FIA 2024 Formula One Sporting Regulations: [FIA PDF](https://api.fia.com/sites/default/files/fia_2024_formula_1_sporting_regulations_-_issue_7_-_2024-07-31.pdf)
- Example F1 strategy paper describing fuel-weight correction: [Formula One Race Strategy, Royal Academy of Engineering / McLaren](https://assets.ctfassets.net/pc40tpn1u6ef/file-8209/a65d908d0b5a68fed86e6ec0c0e19053/550-14_Car_Racing.pdf)
- Example research simulator using a 0.03 ± 0.01 seconds/kg range and a linear fuel model: [Race strategy simulator thesis](https://www.diva-portal.org/smash/get/diva2%3A1763095/FULLTEXT01.pdf)
- Bahrain fuel consumption reference used for the 1.7 kg/lap assumption: [Bahrain International Circuit track information](https://www.racefans.net/f1-information/going-to-a-race/bahrain-international-circuit-track-information/)

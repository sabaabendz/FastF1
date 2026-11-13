# Phase 5: Pit-window simulator

## Goal and scope

Compare candidate strategies by summing predicted lap times and adding a pit-loss estimate. The current prototype simulates 57-lap Bahrain 2024 dry-race plans with one or two stops. It is an educational simulator, not a live team strategy tool.

## Run it

The Phase 3 cleaning script must create the audit CSV first:

```powershell
python scripts/clean_race_data.py
python scripts/simulate_pit_strategy.py
```

The full ranking is saved to `reports/bahrain_2024_strategy_results.csv` (generated output, ignored by Git).

## How it works

1. Read laps marked as suitable for the degradation model.
2. Fit a simple linear model to fuel-corrected lap times. It uses compound, tyre age, and a Soft-specific age feature. This gives Hard and Soft separate age slopes, unlike the Phase 4 baseline that used one shared slope.
3. Enumerate one-stop and two-stop plans, with at least five laps per stint. Every plan includes at least two dry compounds, matching the dry-race requirement in Article 30.5(m) of the [2024 FIA Sporting Regulations](https://api.fia.com/sites/default/files/fia_2024_formula_1_sporting_regulations_-_issue_7_-_2024-07-31.pdf). Bahrain's sample has Hard and Soft stints, but no Medium data.
4. For every simulated lap, predict a fuel-corrected time based on compound and tyre age, then add the estimated fuel penalty back. Add the assumed pit cost once per stop and rank the strategies by estimated total time.
5. Count how many predicted tyre ages are beyond the ages observed in the eligible training data. The report shows both the fastest overall option and the fastest option within the observed age range.

The simulator fits on all eligible laps from the same race. That is useful for making an illustrative curve, but it is not an independent test and is optimistic as a pre-race forecast. The age interaction is used for strategy calculations but has not yet been validated as a separate model against held-out drivers.

## Pit-loss assumption

The script uses 24.8 seconds per stop, the median `lane_duration` among Bahrain's 43 pit records. OpenF1 defines `lane_duration` as the time spent in the pit lane, not the extra time lost compared with driving that section on track. This is therefore a rough proxy, not a measured net pit loss. [OpenF1 pit endpoint](https://openf1.org/docs/#pit)

The same cost is charged for every stop. This does not affect which lap wins among strategies with the same number of stops, but it can change whether one or two stops appears faster. A better estimate needs a true circuit-specific time-loss delta.

## Verified result

The script evaluates **5,772** plans: one-stop and two-stop plans with five or more laps per stint and at least two dry compounds.

- Fastest overall: one stop after lap 34, Soft then Hard, estimated at 5,566.190 seconds. It relies on **14 tyre-age predictions beyond observed data**.
- Fastest plan within observed tyre ages: two stops after laps 18 and 38, Hard–Soft–Hard, estimated at 5,575.219 seconds, with no out-of-range ages.

The roughly nine-second difference does **not** establish that one stop is better. It mostly compares an extrapolated estimate with a plan supported by observed age ranges; it is also sensitive to pit-loss and fuel assumptions. Use the second result as the safer data-supported comparison, not as a guaranteed optimum.

## Limitations

- Only one race is available, and its sample has no Medium compound stints.
- Driver pace, car performance, traffic, tyre warm-up, and strategic interactions are not modeled.
- Stint lengths of at least five laps are a simple simulator guardrail, not a sporting rule.
- There is no limit on how many tyre sets of each compound a team has available.
- Pit loss is only proxied by pit-lane duration. The number of stops can therefore be ranked unreliably.
- Any strategy using tyre ages beyond the observed range requires model extrapolation. This is explicitly counted in the result file.
- Fuel load is still estimated with the Phase 3 assumptions.

## Code map

- `load_eligible_laps` reads and filters the cleaning audit.
- `make_stint_laps` creates hypothetical compound/age rows for each stint.
- `add_compound_age_feature` encodes an age interaction so Soft can have a different wear slope from Hard.
- `build_strategy_model` defines the linear model used by the simulator.
- `simulate_strategies` fits the model, enumerates candidate stop laps and compounds, predicts total time, and marks extrapolated tyre ages.
- `main` saves the full ranking and prints the fastest overall and in-range plans.

## Phase status

The Phase 5 simulator prototype is complete. Improving it further will require more race data and better pit-loss measurements. The Streamlit dashboard and Docker packaging are documented in [Phase 6](phase6.md). A leave-one-driver-out replay comparison for all classified Bahrain 2024 drivers is documented in [actual_comparison.md](actual_comparison.md); it is retrospective and not an independent pre-race forecast.

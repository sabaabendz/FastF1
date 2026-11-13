# Phase 5: Pit-window simulator

## Step 1: One-stop strategy prototype

The prototype enumerates one-stop plans for the 57-lap 2024 Bahrain Grand Prix. It tries every pit lap that leaves at least five laps in each stint, in both compound orders: Hard-to-Soft and Soft-to-Hard. The compounds must differ because the 2024 dry-race rule required at least two dry-weather tyre specifications unless intermediate or wet tyres were used. See Article 30.5(m) of the [2024 FIA Sporting Regulations](https://api.fia.com/sites/default/files/fia_2024_formula_1_sporting_regulations_-_issue_7_-_2024-07-31.pdf).

Run Phase 3's cleaning step first, then the simulator:

```powershell
python scripts/clean_race_data.py
python scripts/simulate_pit_strategy.py
```

The script fits the selected linear model on all eligible Bahrain laps, then predicts each hypothetical lap using compound and tyre age. It adds the per-lap fuel estimate back to the fuel-corrected predictions, sums all 57 predicted lap times, and adds one pit-loss assumption. Fitting on all race data is appropriate for creating this demonstration's pace curve, but the result is not an independent evaluation or a true pre-race forecast.

## Pit-loss assumption

The script uses 24.8 seconds, the median `lane_duration` among Bahrain's 43 pit records. OpenF1 defines `lane_duration` as time spent in the pit lane, not the measured time lost compared with driving the same section of track. We therefore use it as a rough pit-loss proxy, not as a precise delta. A more accurate simulator should estimate pit loss by comparing pit-lap times with representative non-pit laps or use a published circuit-specific loss measurement. Changing a single constant pit cost shifts all one-stop strategies equally, so it does not affect the best one-stop pit lap in this prototype. It would affect comparisons between one-stop and multi-stop plans.

## Verified illustrative output

The script evaluates 96 plans (48 pit laps in each compound order) and writes `reports/bahrain_2024_strategy_results.csv`.

The top-ranked plans are Hard-to-Soft with the stop after lap 29, and Soft-to-Hard after lap 28. Their estimated totals are effectively tied at 5,574.112 seconds. This tie is not meaningful precision: both leading plans require eight tyre-age predictions beyond the maximum age observed for that compound in the eligible Bahrain training data.

The result is illustrative only. The linear model uses just compound and tyre age, has only slight predictive improvement over a mean baseline, and was trained on this same single race. It lacks a compound-specific degradation slope, traffic, car/driver pace, starting tyre state, and outlap warm-up cost. The model's linear trend also extrapolates past observed tyre ages. Those gaps can change the strategy ranking, so the output should not be treated as a real recommendation for an F1 team.

## Code map

- `load_eligible_laps` reads the generated cleaning audit and filters to eligible rows.
- `make_stint_laps` creates the hypothetical compound and tyre-age values the model needs.
- `simulate_one_stop_strategies` fits the linear model, evaluates each stop lap and compound order, adds fuel and pit-loss estimates, and counts out-of-range tyre-age predictions.
- `main` saves the complete ranking and prints the fastest illustrative options.

## Next improvements

Before presenting strategy results as useful, improve the degradation model to estimate compound-specific tyre-age effects, calibrate pit loss as a true time delta, and validate on additional races. A later simulator iteration can enumerate multiple stops and add warm-up/outlap penalties, tyre-set availability, and race conditions.

## References

- [OpenF1 pit endpoint fields](https://openf1.org/docs/#pit): defines `lane_duration` and `stop_duration`.
- [2024 FIA Formula One Sporting Regulations](https://api.fia.com/sites/default/files/fia_2024_formula_1_sporting_regulations_-_issue_7_-_2024-07-31.pdf): dry-weather tyre requirement.

# Bahrain 2024: model replay versus the actual race

## What we compare

The official FIA classification lists Max Verstappen as the winner in **1:31:44.742** over 57 laps. The FIA race report records his observed strategy as Soft–Hard–Soft, pitting after laps 17 and 37. Those stints lasted 17, 20, and 20 laps.

The simulator's ranking includes the same stop laps and compound sequence. Its estimated elapsed time is **1:32:57.612**, which is **72.870 seconds (+1.324%) slower** than the official race time. This is a useful diagnostic: the current simulator does not reproduce the observed winning elapsed time closely.

The fastest strategy within the simulator's observed tyre-age limits is Hard–Soft–Hard, pitting after laps 18 and 38, estimated at **1:32:55.219**. The model estimates this plan to be about 2.4 seconds faster than its replay of Verstappen's actual strategy. It is a counterfactual estimate; this plan was not driven in the race, so we do not know its real finish time.

## How to regenerate the comparison

Run the race loading and cleaning steps first, then:

```powershell
python scripts/simulate_pit_strategy.py
python scripts/compare_actual_result.py
```

The comparison is saved to `reports/bahrain_2024_actual_comparison.csv` and displayed in the Streamlit dashboard. The actual classification and pit strategy are transcribed from the official [FIA classification](https://api.fia.com/sites/default/files/doc_32_-_2024_bahrain_grand_prix_-_final_race_classification.pdf) and [FIA race report](https://api.fia.com/news/f1-verstappen-takes-bahrain-win-ahead-perez-red-bull-seal-1-2-finish).

## What the gap means (and does not mean)

This is a retrospective replay, not an independent prediction test. The degradation model was fitted on eligible laps from the same Bahrain race, including Verstappen's laps. That means the model has already seen some of the data it is being compared against. The result is therefore in-sample and can look more accurate than a genuine pre-race forecast.

The simulator also uses a simple fuel correction and a fixed 24.8-second pit-loss proxy. It assumes each stint starts at tyre age one; Verstappen's opening Soft set was already used, so even this replay does not reproduce the exact tyre state. Its lap model does not represent each driver's underlying pace, car performance, traffic, tyre warm-up, overtaking, or race incidents. The official classification time is the elapsed time of a real race; the simulator total is assembled from estimated lap times and those simplified assumptions.

More training iterations on the same one-race data will not fix these limitations. The next model improvement should add multiple races and test on a race that was completely held out from training. For a pre-race question, training data must come only from earlier events. Compare lap-time MAE/RMSE and the race-time gap on these unseen races before changing model complexity.

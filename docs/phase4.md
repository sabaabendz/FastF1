# Phase 4: Tyre-degradation model

## Step 1: Baseline model comparison

The models estimate a fuel-corrected lap time from tyre compound and tyre age. We compare a simple linear regression with a Random Forest and a mean-only baseline. The linear model is easy to interpret; the forest can learn curved relationships but has more flexibility to overfit.

The data preparation script from Phase 3 must run first because it creates the audit CSV:

```powershell
python scripts/clean_race_data.py
python scripts/train_baseline_model.py
```

The training script uses scikit-learn's `Pipeline` to keep categorical preprocessing and each model together. `OneHotEncoder` turns the text compound (Soft/Hard) into a numeric indicator. Tyre age remains numeric. The target is `fuel_corrected_lap_time`; the raw lap time is retained in the audit. Both models use exactly the same inputs and data split.

The Random Forest has 300 trees and requires at least five training rows in each leaf. A forest averages many decision trees; the leaf-size limit makes each tree less likely to fit tiny groups of laps. `random_state=42` makes the model repeatable, while `n_jobs=-1` lets it use the available processor cores.

## Evaluation split

The script reserves 25% of drivers for testing with a fixed random seed. `GroupShuffleSplit` keeps every lap from one driver on one side of the split, so correlated laps from the same driver cannot appear in both training and test sets. The test drivers for this run were 1, 2, 18, 44, and 63. This tests prediction for drivers the model did not train on; it is a deliberately difficult evaluation and is not equivalent to testing on a future race.

Only one race is available, so this split cannot test generalization to a different circuit, year, weather pattern, or race. It is also possible for multiple drivers from one team to land on opposite sides, so this is not a fully independent team-level test.

## Metrics

- **MAE (Mean Absolute Error):** average size of the prediction error in seconds. It is easy to interpret and treats errors proportionally.
- **RMSE (Root Mean Squared Error):** also in seconds, but squares each error first, so unusually large mistakes count more.
- **R²:** compares squared prediction error with the variation around the test-set mean. A negative value means the predictions are worse than that idealized test-mean reference; it does not mean an error of negative seconds.

The script also compares against a `DummyRegressor` that always predicts the average training lap time. This checks whether using compound and tyre age adds value over a very simple guess.

## Verified baseline result

Using 1,024 eligible laps: 768 training laps and 256 test laps.

| Model | MAE | RMSE | R² |
| --- | ---: | ---: | ---: |
| Linear regression: compound + tyre age | 0.807 s | 1.052 s | -0.069 |
| Random Forest: compound + tyre age | 0.812 s | 1.056 s | -0.075 |
| Mean-only training baseline | 0.822 s | 1.082 s | — |

Both models are only slightly better than the mean-only baseline. The Random Forest is marginally worse than the linear model on this split, so its extra complexity did not help. Both R² values are negative, meaning neither model explains the held-out drivers' lap-time variation well. Car and driver pace differ, and neither effect is represented by the two input features. This result is not strong evidence that tyre age has no effect; it shows that these features and this single-race dataset are not enough for accurate unseen-driver lap-time prediction.

Test predictions are written to `reports/baseline_predictions.csv`, which is generated and ignored by Git. This makes individual errors inspectable without committing derived output files.

## Limitations and next model

The target uses the Phase 3 fuel estimate (1.7 kg/lap and 0.03 seconds/kg), so model results depend on those assumptions. Bahrain 2024 provides only Hard and Soft compounds. The yellow-flag laps remain included, and traffic, driver pace, car setup, track evolution, and fuel saving are not fully captured. Model comparisons must reuse the same group split and target so the scores are comparable.

Next in this phase: decide whether to add more explanatory features before trying XGBoost. With only one race and these two inputs, comparing increasingly complex models may mostly compare their ability to fit this small dataset rather than learn transferable tyre behaviour.

## References

- [scikit-learn model evaluation metrics](https://scikit-learn.org/stable/modules/model_evaluation.html)
- [scikit-learn GroupShuffleSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html)
- [scikit-learn ColumnTransformer](https://scikit-learn.org/stable/modules/generated/sklearn.compose.ColumnTransformer.html)
- [scikit-learn RandomForestRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html)

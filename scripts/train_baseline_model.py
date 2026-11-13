"""Train and evaluate a simple tyre-age lap-time regression model."""

from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "reports" / "bahrain_2024_cleaning_audit.csv"
PREDICTIONS_PATH = PROJECT_ROOT / "reports" / "baseline_predictions.csv"
FEATURE_COLUMNS = ["compound", "tyre_age"]
TARGET_COLUMN = "fuel_corrected_lap_time"
GROUP_COLUMN = "driver_number"


def load_model_data() -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Load only eligible laps and return features, target, and driver groups."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Cleaning audit is missing. Run scripts/clean_race_data.py first."
        )

    audit = pd.read_csv(DATA_PATH)
    eligible = audit.loc[audit["keep_for_degradation_model"]].copy()
    eligible = eligible.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN, GROUP_COLUMN])

    features = eligible[FEATURE_COLUMNS]
    target = eligible[TARGET_COLUMN]
    driver_groups = eligible[GROUP_COLUMN]
    return features, target, driver_groups


def build_model() -> Pipeline:
    """Create preprocessing and linear regression as one reusable pipeline."""
    preprocess = ColumnTransformer(
        transformers=[
            (
                "compound",
                OneHotEncoder(drop="first", handle_unknown="ignore"),
                ["compound"],
            ),
            ("tyre_age", "passthrough", ["tyre_age"]),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocess),
            ("regression", LinearRegression()),
        ]
    )


def main() -> None:
    features, target, driver_groups = load_model_data()
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_indices, test_indices = next(
        splitter.split(features, target, groups=driver_groups)
    )

    train_features = features.iloc[train_indices]
    test_features = features.iloc[test_indices]
    train_target = target.iloc[train_indices]
    test_target = target.iloc[test_indices]
    test_drivers = driver_groups.iloc[test_indices]

    model = build_model()
    model.fit(train_features, train_target)
    predictions = model.predict(test_features)

    # A mean-only predictor checks whether the useful features beat a trivial guess.
    mean_baseline = DummyRegressor(strategy="mean")
    mean_baseline.fit(train_features, train_target)
    baseline_predictions = mean_baseline.predict(test_features)

    model_rmse = mean_squared_error(test_target, predictions) ** 0.5
    baseline_rmse = mean_squared_error(test_target, baseline_predictions) ** 0.5
    print(f"Eligible laps: {len(features)}")
    print(f"Training laps: {len(train_indices)}")
    print(f"Test laps: {len(test_indices)}")
    print(f"Test drivers: {sorted(test_drivers.unique().astype(int).tolist())}")
    print("Metrics on drivers held out from training:")
    print(f"  Linear regression MAE: {mean_absolute_error(test_target, predictions):.3f} s")
    print(f"  Linear regression RMSE: {model_rmse:.3f} s")
    print(f"  Linear regression R²: {r2_score(test_target, predictions):.3f}")
    print(f"  Mean-only baseline MAE: {mean_absolute_error(test_target, baseline_predictions):.3f} s")
    print(f"  Mean-only baseline RMSE: {baseline_rmse:.3f} s")

    prediction_report = pd.DataFrame(
        {
            "driver_number": test_drivers.to_numpy(),
            "compound": test_features["compound"].to_numpy(),
            "tyre_age": test_features["tyre_age"].to_numpy(),
            "actual_fuel_corrected_lap_time": test_target.to_numpy(),
            "linear_prediction": predictions,
            "mean_baseline_prediction": baseline_predictions,
        }
    )
    prediction_report.to_csv(PREDICTIONS_PATH, index=False)
    print(f"Saved test predictions: {PREDICTIONS_PATH}")


if __name__ == "__main__":
    main()

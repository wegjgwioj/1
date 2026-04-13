# coding:utf-8
import json
import os
import warnings

import joblib
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler

from .evaluation import regression_metrics
from .feature_engineering import TARGET_COLUMNS, get_feature_columns, resolve_training_dataframe


def _make_preprocessor():
    feature_columns = get_feature_columns()
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                    ]
                ),
                feature_columns["numeric"],
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                feature_columns["categorical"],
            ),
        ]
    )


def _make_model_bundle(estimator, scale_sparse=False):
    steps = [("preprocessor", _make_preprocessor())]
    if scale_sparse:
        steps.append(("scaler", StandardScaler(with_mean=False)))
    steps.append(("model", estimator))
    return Pipeline(steps=steps)


def _train_estimator_set(frame, estimators):
    feature_columns = get_feature_columns()
    metrics = {}
    models = {}

    for name, estimator_template in estimators.items():
        target = TARGET_COLUMNS["power"] if name.startswith("power") else TARGET_COLUMNS["life"]
        target_frame = frame.dropna(subset=[target])
        if len(target_frame) < 3:
            continue
        target_X = target_frame[feature_columns["numeric"] + feature_columns["categorical"]]
        target_y = target_frame[target]
        estimator = clone(estimator_template)

        if len(target_frame) >= 8:
            x_train, x_test, y_train, y_test = train_test_split(
                target_X,
                target_y,
                test_size=0.2,
                random_state=42,
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=ConvergenceWarning)
                estimator.fit(x_train, y_train)
            y_pred = estimator.predict(x_test)
            evaluation_mode = "holdout"
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=ConvergenceWarning)
                estimator.fit(target_X, target_y)
            y_pred = estimator.predict(target_X)
            y_test = target_y
            evaluation_mode = "train_set_proxy"

        metrics[name] = {
            "target": target,
            "sample_count": int(len(target_frame)),
            "evaluation_mode": evaluation_mode,
            **regression_metrics(y_test, y_pred),
        }
        if evaluation_mode == "holdout":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=ConvergenceWarning)
                estimator.fit(target_X, target_y)
        models[name] = estimator

    return models, metrics


def train_ml_bundle(queryset_or_records=None, excel_path=None, source="auto"):
    frame, source_info = resolve_training_dataframe(
        queryset_or_records=queryset_or_records,
        excel_path=excel_path,
        source=source,
    )
    if frame.empty or len(frame) < 3:
        raise ValueError("可用于训练的有效样本不足，至少需要 3 条。")

    estimators = {
        "power": _make_model_bundle(RandomForestRegressor(n_estimators=200, random_state=42)),
        "life": _make_model_bundle(GradientBoostingRegressor(random_state=42)),
    }
    models, metrics = _train_estimator_set(frame, estimators)

    if not models:
        raise ValueError("没有满足训练条件的目标列数据。")

    return models, metrics, source_info


def train_neural_baseline_bundle(queryset_or_records=None, excel_path=None, source="auto"):
    frame, source_info = resolve_training_dataframe(
        queryset_or_records=queryset_or_records,
        excel_path=excel_path,
        source=source,
    )
    if frame.empty or len(frame) < 3:
        raise ValueError("可用于训练神经网络基线的有效样本不足，至少需要 3 条。")

    estimators = {
        "power_mlp": _make_model_bundle(
            MLPRegressor(hidden_layer_sizes=(64, 32), activation="relu", random_state=42, max_iter=1500),
            scale_sparse=True,
        ),
        "life_mlp": _make_model_bundle(
            MLPRegressor(hidden_layer_sizes=(32, 16), activation="relu", random_state=42, max_iter=1500),
            scale_sparse=True,
        ),
    }
    models, metrics = _train_estimator_set(frame, estimators)
    if not models:
        raise ValueError("没有满足训练条件的神经网络基线目标列数据。")
    return models, metrics, source_info


def save_ml_artifacts(models, metrics, base_dir, comparison_models=None, comparison_metrics=None, manifest=None):
    artifact_dir = os.path.join(base_dir, "artifacts")
    model_dir = os.path.join(artifact_dir, "models")
    report_dir = os.path.join(artifact_dir, "reports")
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)

    output_paths = {}
    if "power" in models:
        output_paths["power_model"] = os.path.join(model_dir, "drivinglog_power_model.pkl")
        joblib.dump(models["power"], output_paths["power_model"])
    if "life" in models:
        output_paths["life_model"] = os.path.join(model_dir, "drivinglog_life_model.pkl")
        joblib.dump(models["life"], output_paths["life_model"])
    if comparison_models and "power_mlp" in comparison_models:
        output_paths["power_mlp_model"] = os.path.join(model_dir, "drivinglog_power_mlp_model.pkl")
        joblib.dump(comparison_models["power_mlp"], output_paths["power_mlp_model"])
    if comparison_models and "life_mlp" in comparison_models:
        output_paths["life_mlp_model"] = os.path.join(model_dir, "drivinglog_life_mlp_model.pkl")
        joblib.dump(comparison_models["life_mlp"], output_paths["life_mlp_model"])

    output_paths["metrics"] = os.path.join(report_dir, "ml_metrics.json")
    with open(output_paths["metrics"], "w", encoding="utf-8") as metrics_file:
        json.dump(metrics, metrics_file, ensure_ascii=False, indent=2)

    if comparison_metrics:
        output_paths["comparison_metrics"] = os.path.join(report_dir, "ml_comparison_metrics.json")
        with open(output_paths["comparison_metrics"], "w", encoding="utf-8") as metrics_file:
            json.dump(comparison_metrics, metrics_file, ensure_ascii=False, indent=2)

    if manifest:
        output_paths["manifest"] = os.path.join(report_dir, "ml_bundle_manifest.json")
        with open(output_paths["manifest"], "w", encoding="utf-8") as manifest_file:
            json.dump(manifest, manifest_file, ensure_ascii=False, indent=2)

    return output_paths

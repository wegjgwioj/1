# coding:utf-8
import json
import os
from datetime import datetime

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import GroupShuffleSplit

from main.ml.evaluation import regression_metrics

from .nasa_dataset import NASA_BATTERY_DATASET_NAME, get_battery_life_artifact_paths


SOH_FEATURE_COLUMNS = [
    "cycle_index",
    "voltage_mean",
    "current_mean",
    "temperature_mean",
    "duration_seconds",
]

RUL_FEATURE_COLUMNS = [
    "cycle_index",
    "capacity",
    "voltage_mean",
    "current_mean",
    "temperature_mean",
    "duration_seconds",
]


def _coerce_frame(rows_or_frame):
    frame = rows_or_frame.copy() if isinstance(rows_or_frame, pd.DataFrame) else pd.DataFrame(list(rows_or_frame))
    for column in sorted(set(SOH_FEATURE_COLUMNS + RUL_FEATURE_COLUMNS + ["soh", "rul"])):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.dropna(subset=RUL_FEATURE_COLUMNS + ["soh", "rul", "battery_id"]).reset_index(drop=True)


def _split_group_holdout(frame):
    battery_ids = frame["battery_id"].astype(str)
    unique_batteries = battery_ids.nunique()
    if unique_batteries < 2 or len(frame) < 8:
        return None, None, "train_set_proxy", sorted(battery_ids.unique().tolist()), []

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_index, test_index = next(splitter.split(frame, groups=battery_ids))
    train_frame = frame.iloc[train_index].reset_index(drop=True)
    test_frame = frame.iloc[test_index].reset_index(drop=True)
    if train_frame.empty or test_frame.empty:
        return None, None, "train_set_proxy", sorted(battery_ids.unique().tolist()), []
    train_batteries = sorted(train_frame["battery_id"].astype(str).unique().tolist())
    test_batteries = sorted(test_frame["battery_id"].astype(str).unique().tolist())
    return train_frame, test_frame, "group_holdout", train_batteries, test_batteries


def _train_target(frame, target_name, estimator, feature_columns):
    x_data = frame[feature_columns]
    y_data = frame[target_name]
    train_frame, test_frame, evaluation_mode, train_batteries, test_batteries = _split_group_holdout(frame)
    if evaluation_mode == "group_holdout":
        estimator.fit(train_frame[feature_columns], train_frame[target_name])
        y_test = test_frame[target_name]
        y_pred = estimator.predict(test_frame[feature_columns])
        estimator.fit(x_data, y_data)
    else:
        estimator.fit(x_data, y_data)
        y_test = y_data
        y_pred = estimator.predict(x_data)

    metrics = {
        "target": target_name,
        "sample_count": int(len(frame)),
        "evaluation_mode": evaluation_mode,
        "train_battery_count": len(train_batteries),
        "test_battery_count": len(test_batteries),
        **regression_metrics(y_test, y_pred),
    }
    split_info = {
        "train_batteries": train_batteries,
        "test_batteries": test_batteries,
    }
    return estimator, metrics, y_test, y_pred, split_info


def _plot_capacity_curve(frame, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.figure(figsize=(10, 5))
    for battery_id, group in frame.groupby("battery_id"):
        group = group.sort_values("cycle_index")
        plt.plot(group["cycle_index"], group["capacity"], linewidth=1, alpha=0.65, label=str(battery_id))
    plt.axhline(1.4, color="red", linestyle="--", linewidth=1, label="EOL 1.4Ah")
    plt.xlabel("Cycle")
    plt.ylabel("Capacity (Ah)")
    plt.title("NASA Battery Capacity Degradation")
    plt.legend(fontsize=6, ncol=4)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _plot_prediction(y_true, y_pred, target_name, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.figure(figsize=(5, 5))
    plt.scatter(y_true, y_pred, s=12, alpha=0.65)
    min_value = min(float(min(y_true)), float(min(y_pred)))
    max_value = max(float(max(y_true)), float(max(y_pred)))
    plt.plot([min_value, max_value], [min_value, max_value], color="red", linestyle="--", linewidth=1)
    plt.xlabel("True")
    plt.ylabel("Predicted")
    plt.title(f"NASA {target_name.upper()} Prediction")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def train_real_life_models(rows_or_frame, base_dir=None):
    frame = _coerce_frame(rows_or_frame)
    if len(frame) < 3:
        raise ValueError("真实寿命实验有效样本不足，至少需要 3 条 NASA discharge 循环记录。")

    paths = get_battery_life_artifact_paths(base_dir)
    os.makedirs(paths["artifact_dir"], exist_ok=True)
    os.makedirs(paths["figure_dir"], exist_ok=True)

    soh_model, soh_metrics, soh_true, soh_pred, soh_split = _train_target(
        frame,
        "soh",
        RandomForestRegressor(n_estimators=200, random_state=42),
        SOH_FEATURE_COLUMNS,
    )
    rul_model, rul_metrics, rul_true, rul_pred, rul_split = _train_target(
        frame,
        "rul",
        GradientBoostingRegressor(random_state=42),
        RUL_FEATURE_COLUMNS,
    )

    joblib.dump(soh_model, paths["soh_model"])
    joblib.dump(rul_model, paths["rul_model"])

    metrics = {
        "soh": soh_metrics,
        "rul": rul_metrics,
    }
    with open(paths["metrics"], "w", encoding="utf-8") as metrics_file:
        json.dump(metrics, metrics_file, ensure_ascii=False, indent=2)

    _plot_capacity_curve(frame, paths["capacity_curve"])
    _plot_prediction(soh_true, soh_pred, "soh", paths["soh_prediction_plot"])
    _plot_prediction(rul_true, rul_pred, "rul", paths["rul_prediction_plot"])

    manifest = {
        "dataset": NASA_BATTERY_DATASET_NAME,
        "model_family": "RandomForest(SOH)+GradientBoosting(RUL)",
        "split_strategy": "group_holdout_by_battery" if soh_metrics["evaluation_mode"] == "group_holdout" else "train_set_proxy",
        "feature_columns": {
            "soh": SOH_FEATURE_COLUMNS,
            "rul": RUL_FEATURE_COLUMNS,
        },
        "train_batteries": soh_split["train_batteries"],
        "test_batteries": soh_split["test_batteries"],
        "figures": {
            "capacity_curve": paths["capacity_curve"],
            "soh_prediction_plot": paths["soh_prediction_plot"],
            "rul_prediction_plot": paths["rul_prediction_plot"],
        },
        "sample_count": int(len(frame)),
        "battery_count": int(frame["battery_id"].nunique()) if "battery_id" in frame.columns else 0,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(paths["training_manifest"], "w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, ensure_ascii=False, indent=2)

    return {
        "paths": paths,
        "metrics": metrics,
        "manifest": manifest,
    }

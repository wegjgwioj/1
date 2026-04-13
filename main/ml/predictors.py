# coding:utf-8
import json
import os
from datetime import datetime

import joblib
import pandas as pd

from main.models import drivinglog, drivinglogforecast
from main.excel_sources import resolve_default_raw_telemetry_excel

from .feature_engineering import (
    CATEGORICAL_FEATURES,
    NUMERIC_DEFAULTS,
    NUMERIC_FEATURES,
    fill_missing_targets,
)
from .trainers import save_ml_artifacts, train_ml_bundle, train_neural_baseline_bundle


MODEL_NAME_MAP = {
    "power": "RandomForestRegressor",
    "life": "GradientBoostingRegressor",
}


def get_artifact_paths(base_dir=None):
    root_dir = base_dir or os.getcwd()
    artifact_dir = os.path.join(root_dir, "artifacts")
    return {
        "artifact_dir": artifact_dir,
        "model_dir": os.path.join(artifact_dir, "models"),
        "report_dir": os.path.join(artifact_dir, "reports"),
        "power_model": os.path.join(artifact_dir, "models", "drivinglog_power_model.pkl"),
        "life_model": os.path.join(artifact_dir, "models", "drivinglog_life_model.pkl"),
        "power_mlp_model": os.path.join(artifact_dir, "models", "drivinglog_power_mlp_model.pkl"),
        "life_mlp_model": os.path.join(artifact_dir, "models", "drivinglog_life_mlp_model.pkl"),
        "metrics": os.path.join(artifact_dir, "reports", "ml_metrics.json"),
        "comparison_metrics": os.path.join(artifact_dir, "reports", "ml_comparison_metrics.json"),
        "manifest": os.path.join(artifact_dir, "reports", "ml_bundle_manifest.json"),
    }


def ensure_ml_artifacts(force_retrain=False, queryset=None, base_dir=None, excel_path=None, source="auto"):
    paths = get_artifact_paths(base_dir)
    need_train = force_retrain or not os.path.exists(paths["metrics"])
    need_train = need_train or (
        not os.path.exists(paths["power_model"]) and not os.path.exists(paths["life_model"])
    )
    need_train = need_train or not os.path.exists(paths["comparison_metrics"])
    need_train = need_train or (
        not os.path.exists(paths["power_mlp_model"]) and not os.path.exists(paths["life_mlp_model"])
    )
    need_train = need_train or not os.path.exists(paths["manifest"])
    if need_train:
        training_queryset = queryset or drivinglog.objects.all()
        resolved_excel = excel_path or resolve_default_raw_telemetry_excel(base_dir)
        models, metrics, source_info = train_ml_bundle(
            queryset_or_records=training_queryset,
            excel_path=resolved_excel,
            source=source,
        )
        comparison_models, comparison_metrics, _ = train_neural_baseline_bundle(
            queryset_or_records=training_queryset,
            excel_path=resolved_excel,
            source=source,
        )
        timestamp = datetime.now()
        save_ml_artifacts(
            models,
            metrics,
            base_dir or os.getcwd(),
            comparison_models=comparison_models,
            comparison_metrics=comparison_metrics,
            manifest={
                **source_info,
                "updated_at": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "version": timestamp.strftime("ml-%Y%m%d%H%M%S"),
            },
        )
    return paths


def load_ml_bundle(force_retrain=False, queryset=None, base_dir=None, excel_path=None, source="auto"):
    paths = ensure_ml_artifacts(
        force_retrain=force_retrain,
        queryset=queryset,
        base_dir=base_dir,
        excel_path=excel_path,
        source=source,
    )

    models = {}
    if os.path.exists(paths["power_model"]):
        models["power"] = joblib.load(paths["power_model"])
    if os.path.exists(paths["life_model"]):
        models["life"] = joblib.load(paths["life_model"])

    with open(paths["metrics"], "r", encoding="utf-8") as metrics_file:
        metrics = json.load(metrics_file)
    comparison_metrics = {}
    if os.path.exists(paths["comparison_metrics"]):
        with open(paths["comparison_metrics"], "r", encoding="utf-8") as metrics_file:
            comparison_metrics = json.load(metrics_file)

    manifest = {}
    if os.path.exists(paths["manifest"]):
        with open(paths["manifest"], "r", encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)
    updated_at = manifest.get("updated_at") or datetime.fromtimestamp(os.path.getmtime(paths["metrics"])).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    version = manifest.get("version") or datetime.fromtimestamp(os.path.getmtime(paths["metrics"])).strftime(
        "ml-%Y%m%d%H%M%S"
    )
    return {
        "models": models,
        "metrics": metrics,
        "comparison_metrics": comparison_metrics,
        "paths": paths,
        "updated_at": updated_at,
        "version": version,
        "source_type": manifest.get("source_type", "drivinglog_table"),
        "source_excel": manifest.get("source_excel", ""),
        "sample_count": manifest.get("sample_count"),
    }


def normalize_prediction_payload(payload):
    payload = payload or {}
    record = {}
    for column in NUMERIC_FEATURES:
        value = payload.get(column, NUMERIC_DEFAULTS[column])
        if value in (None, ""):
            value = NUMERIC_DEFAULTS[column]
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = NUMERIC_DEFAULTS[column]
        record[column] = value

    record["batterycapacity"] = max(record["batterycapacity"], 1)
    record["accumulatedmileage"] = max(record["accumulatedmileage"], 0)
    record["averagespeed"] = min(max(record["averagespeed"], 0), 160)
    record["batterylevel"] = min(max(record["batterylevel"], 0), 100)
    record["rapidaccelerationtimes"] = max(record["rapidaccelerationtimes"], 0)
    record["numberofrapiddecelerations"] = max(record["numberofrapiddecelerations"], 0)
    record["numberofspeedingincidents"] = max(record["numberofspeedingincidents"], 0)
    record["drivingbehaviorrating"] = min(max(record["drivingbehaviorrating"], 0), 100)

    for column in CATEGORICAL_FEATURES:
        value = payload.get(column)
        if value in (None, ""):
            value = "综合工况" if column == "drivingroute" else "标准车型"
        record[column] = str(value)

    return record


def _build_prediction_frame(record):
    frame = pd.DataFrame([record])
    for column in NUMERIC_FEATURES:
        if column not in frame.columns:
            frame[column] = NUMERIC_DEFAULTS[column]
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(NUMERIC_DEFAULTS[column])
    for column in CATEGORICAL_FEATURES:
        if column not in frame.columns:
            frame[column] = ""
        frame[column] = frame[column].fillna("").astype(str)
    return frame


def _fallback_predictions(frame):
    enriched = frame.copy()
    enriched["powerconsumption"] = None
    enriched["batterylife"] = None
    enriched = fill_missing_targets(enriched)
    row = enriched.iloc[0]
    return float(row["powerconsumption"]), int(round(row["batterylife"]))


def _build_major_factors(record, predicted_power, predicted_life):
    scored_reasons = []
    if record["drivingbehaviorrating"] < 70:
        scored_reasons.append((3, "驾驶行为评分偏低，说明急加速或急减速较多。"))
    if record["numberofspeedingincidents"] > 0:
        scored_reasons.append((3, "存在超速事件，能耗和电池压力都会上升。"))
    if record["rapidaccelerationtimes"] >= 3:
        scored_reasons.append((2, "急加速次数偏多，短时功率需求较高。"))
    if record["batterylevel"] < 30:
        scored_reasons.append((2, "当前电池余量偏低，续航风险更敏感。"))
    if record["averagespeed"] > 85:
        scored_reasons.append((2, "平均车速偏高，高速工况通常会拉高耗电量。"))
    if record["accumulatedmileage"] > 250:
        scored_reasons.append((1, "累计里程较高，需要关注电池衰减趋势。"))
    if predicted_power >= 20:
        scored_reasons.append((2, "预测耗电量偏高，建议优化路线和驾驶习惯。"))
    if predicted_life <= 36:
        scored_reasons.append((2, "预测电池寿命偏低，建议尽快安排电池健康检查。"))

    scored_reasons.sort(key=lambda item: item[0], reverse=True)
    factors = [reason for _, reason in scored_reasons[:3]]
    if not factors:
        factors.append("当前工况整体平稳，预测结果主要受基础里程和容量影响。")
    return factors


def _infer_risk_level(predicted_power, predicted_life):
    if predicted_life <= 30 or predicted_power >= 24:
        return "高"
    if predicted_life <= 48 or predicted_power >= 18:
        return "中"
    return "低"


def _predict_from_bundle(record, bundle):
    frame = _build_prediction_frame(record)
    fallback_power, fallback_life = _fallback_predictions(frame)

    models = bundle["models"]
    predicted_power = fallback_power
    predicted_life = fallback_life
    if "power" in models:
        predicted_power = float(models["power"].predict(frame)[0])
    if "life" in models:
        predicted_life = int(round(float(models["life"].predict(frame)[0])))

    predicted_power = round(max(predicted_power, 0), 2)
    predicted_life = max(predicted_life, 1)
    risk_level = _infer_risk_level(predicted_power, predicted_life)
    major_factors = _build_major_factors(record, predicted_power, predicted_life)

    available_models = [MODEL_NAME_MAP[key] for key in ("power", "life") if key in models]
    model_name = " + ".join(available_models) if available_models else "HeuristicFallback"

    return {
        "vehiclemodel": record["vehiclemodel"],
        "batterycapacity": int(round(record["batterycapacity"])),
        "accumulatedmileage": int(round(record["accumulatedmileage"])),
        "drivingbehaviorrating": int(round(record["drivingbehaviorrating"])),
        "batterylife": predicted_life,
        "predictedpowerconsumption": predicted_power,
        "risklevel": risk_level,
        "modelname": model_name,
        "modelversion": bundle["version"],
        "majorfactors": major_factors,
        "metrics": bundle["metrics"],
        "comparison_metrics": bundle.get("comparison_metrics", {}),
        "updated_at": bundle["updated_at"],
    }


def save_prediction_record(prediction, record_id=None):
    save_data = {
        "vehiclemodel": prediction["vehiclemodel"],
        "batterycapacity": prediction["batterycapacity"],
        "accumulatedmileage": prediction["accumulatedmileage"],
        "drivingbehaviorrating": prediction["drivingbehaviorrating"],
        "batterylife": prediction["batterylife"],
        "predictedpowerconsumption": prediction["predictedpowerconsumption"],
        "risklevel": prediction["risklevel"],
        "modelname": prediction["modelname"],
        "modelversion": prediction["modelversion"],
        "majorfactors": json.dumps(prediction["majorfactors"], ensure_ascii=False),
    }

    if record_id:
        obj = drivinglogforecast.objects.filter(id=record_id).first()
        if obj:
            for key, value in save_data.items():
                setattr(obj, key, value)
            obj.save()
            return obj
    return drivinglogforecast.objects.create(**save_data)


def predict_drivinglog(payload, persist=True, force_retrain=False, queryset=None, base_dir=None):
    bundle = load_ml_bundle(force_retrain=force_retrain, queryset=queryset, base_dir=base_dir)
    record = normalize_prediction_payload(payload)
    prediction = _predict_from_bundle(record, bundle)
    if persist:
        saved = save_prediction_record(prediction, record_id=payload.get("id"))
        prediction["id"] = saved.id
    return prediction


def build_scenario_inputs(payload):
    base_record = normalize_prediction_payload(payload)
    scenarios = [
        {
            "name": "稳健通勤",
            "description": "降低速度波动、减少急加速，模拟更平稳的城市通勤。",
            "input": {
                **base_record,
                "drivingroute": "城市通勤",
                "averagespeed": max(base_record["averagespeed"] - 8, 35),
                "drivingbehaviorrating": min(base_record["drivingbehaviorrating"] + 8, 100),
                "rapidaccelerationtimes": 0,
                "numberofrapiddecelerations": 0,
                "numberofspeedingincidents": 0,
            },
        },
        {
            "name": "高速长途",
            "description": "提高平均车速并延长里程，模拟高速长途工况。",
            "input": {
                **base_record,
                "drivingroute": "高速长途",
                "averagespeed": max(base_record["averagespeed"], 95),
                "accumulatedmileage": base_record["accumulatedmileage"] + 80,
                "drivingbehaviorrating": max(base_record["drivingbehaviorrating"] - 6, 0),
                "numberofspeedingincidents": base_record["numberofspeedingincidents"] + 1,
            },
        },
        {
            "name": "拥堵频启停",
            "description": "低速拥堵且频繁加减速，模拟更差的通勤工况。",
            "input": {
                **base_record,
                "drivingroute": "拥堵路段",
                "averagespeed": min(base_record["averagespeed"], 30),
                "batterylevel": min(base_record["batterylevel"], 25),
                "drivingbehaviorrating": max(base_record["drivingbehaviorrating"] - 12, 0),
                "rapidaccelerationtimes": base_record["rapidaccelerationtimes"] + 2,
                "numberofrapiddecelerations": base_record["numberofrapiddecelerations"] + 3,
                "numberofspeedingincidents": base_record["numberofspeedingincidents"],
            },
        },
    ]
    return base_record, scenarios


def predict_scenarios(payload, force_retrain=False, queryset=None, base_dir=None):
    bundle = load_ml_bundle(force_retrain=force_retrain, queryset=queryset, base_dir=base_dir)
    base_record, scenarios = build_scenario_inputs(payload)
    result = {
        "base_input": base_record,
        "scenarios": [],
        "updated_at": bundle["updated_at"],
        "modelversion": bundle["version"],
    }
    for scenario in scenarios:
        prediction = _predict_from_bundle(scenario["input"], bundle)
        result["scenarios"].append(
            {
                "name": scenario["name"],
                "description": scenario["description"],
                "input": scenario["input"],
                "prediction": prediction,
            }
        )
    return result

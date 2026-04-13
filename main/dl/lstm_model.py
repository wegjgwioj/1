# coding:utf-8
import json
import os
from datetime import datetime

import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from main.ml.evaluation import regression_metrics
from main.ml.predictors import _build_major_factors, _infer_risk_level, normalize_prediction_payload

from .sequence_dataset import build_inference_sequence, load_sequence_dataset, prepare_sequence_dataset


try:  # pragma: no cover - 是否安装 torch 取决于运行环境
    import torch
    from torch import nn

    TORCH_AVAILABLE = True
except Exception:  # pragma: no cover
    torch = None
    nn = None
    TORCH_AVAILABLE = False


if TORCH_AVAILABLE:  # pragma: no cover - 无 torch 时不会执行
    class SequenceRegressor(nn.Module):
        def __init__(self, input_size, hidden_size=24):
            super().__init__()
            self.encoder = nn.GRU(input_size=input_size, hidden_size=hidden_size, batch_first=True)
            self.head = nn.Sequential(
                nn.Linear(hidden_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, 1),
            )

        def forward(self, batch):
            hidden_states, _ = self.encoder(batch)
            output = hidden_states[:, -1, :]
            return self.head(output).squeeze(-1)

else:
    class SequenceRegressor:  # pragma: no cover - 仅用于占位，避免无 torch 时导入失败
        pass


def get_dl_artifact_paths(base_dir=None):
    root_dir = base_dir or os.getcwd()
    artifact_dir = os.path.join(root_dir, "artifacts")
    model_dir = os.path.join(artifact_dir, "models")
    report_dir = os.path.join(artifact_dir, "reports")
    return {
        "artifact_dir": artifact_dir,
        "model_dir": model_dir,
        "report_dir": report_dir,
        "power_torch_model": os.path.join(model_dir, "drivinglog_dl_power_model.pt"),
        "life_torch_model": os.path.join(model_dir, "drivinglog_dl_life_model.pt"),
        "power_fallback_model": os.path.join(model_dir, "drivinglog_dl_power_model.pkl"),
        "life_fallback_model": os.path.join(model_dir, "drivinglog_dl_life_model.pkl"),
        "metrics": os.path.join(report_dir, "dl_metrics.json"),
        "manifest": os.path.join(report_dir, "dl_bundle_manifest.json"),
        "compare": os.path.join(report_dir, "model_compare.json"),
    }


def _fit_fallback_model(x_data, y_data):
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "mlp",
                MLPRegressor(
                    hidden_layer_sizes=(48, 24),
                    random_state=42,
                    max_iter=1500,
                ),
            ),
        ]
    )
    pipeline.fit(x_data, y_data)
    return pipeline


def _train_fallback_target(x_data, y_data):
    flat_x = x_data.reshape(len(x_data), -1)
    if len(flat_x) >= 8:
        x_train, x_test, y_train, y_test = train_test_split(flat_x, y_data, test_size=0.2, random_state=42)
        model = _fit_fallback_model(x_train, y_train)
        y_pred = model.predict(x_test)
        evaluation_mode = "holdout"
    else:
        model = _fit_fallback_model(flat_x, y_data)
        y_test = y_data
        y_pred = model.predict(flat_x)
        evaluation_mode = "train_set_proxy"

    metrics = {
        "sample_count": int(len(flat_x)),
        "evaluation_mode": evaluation_mode,
        **regression_metrics(y_test, y_pred),
    }

    if evaluation_mode == "holdout":
        model = _fit_fallback_model(flat_x, y_data)
    return model, metrics


def _torch_tensor(value):  # pragma: no cover - 无 torch 时不会执行
    return torch.as_tensor(value, dtype=torch.float32)


def _train_torch_target(x_data, y_data, input_size):  # pragma: no cover - 依赖 torch
    epochs = 120
    learning_rate = 0.01

    if len(x_data) >= 8:
        x_train, x_test, y_train, y_test = train_test_split(x_data, y_data, test_size=0.2, random_state=42)
        evaluation_mode = "holdout"
    else:
        x_train, x_test, y_train, y_test = x_data, x_data, y_data, y_data
        evaluation_mode = "train_set_proxy"

    model = SequenceRegressor(input_size=input_size)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()

    train_x = _torch_tensor(x_train)
    train_y = _torch_tensor(y_train)
    for _ in range(epochs):
        optimizer.zero_grad()
        predictions = model(train_x)
        loss = criterion(predictions, train_y)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        predicted = model(_torch_tensor(x_test)).cpu().numpy()

    metrics = {
        "sample_count": int(len(x_data)),
        "evaluation_mode": evaluation_mode,
        **regression_metrics(y_test, predicted),
    }

    if evaluation_mode == "holdout":
        full_x = _torch_tensor(x_data)
        full_y = _torch_tensor(y_data)
        model = SequenceRegressor(input_size=input_size)
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        for _ in range(epochs):
            optimizer.zero_grad()
            predictions = model(full_x)
            loss = criterion(predictions, full_y)
            loss.backward()
            optimizer.step()
    return model, metrics


def train_dl_bundle(queryset_or_records=None, excel_path=None, base_dir=None, force_retrain=False):
    paths = get_dl_artifact_paths(base_dir)
    os.makedirs(paths["model_dir"], exist_ok=True)
    os.makedirs(paths["report_dir"], exist_ok=True)

    dataset_result = prepare_sequence_dataset(
        queryset_or_records=queryset_or_records,
        excel_path=excel_path,
        base_dir=base_dir,
    )
    dataset = load_sequence_dataset(base_dir)
    x_data = dataset["X"]
    input_size = int(x_data.shape[-1])

    if TORCH_AVAILABLE:
        backend = "pytorch_gru"
        power_model, power_metrics = _train_torch_target(x_data, dataset["y_power"], input_size)
        life_model, life_metrics = _train_torch_target(x_data, dataset["y_life"], input_size)
        torch.save(power_model.state_dict(), paths["power_torch_model"])
        torch.save(life_model.state_dict(), paths["life_torch_model"])
        model_paths = {
            "power": paths["power_torch_model"],
            "life": paths["life_torch_model"],
        }
    else:
        backend = "sklearn_mlp_fallback"
        power_model, power_metrics = _train_fallback_target(x_data, dataset["y_power"])
        life_model, life_metrics = _train_fallback_target(x_data, dataset["y_life"])
        joblib.dump(power_model, paths["power_fallback_model"])
        joblib.dump(life_model, paths["life_fallback_model"])
        model_paths = {
            "power": paths["power_fallback_model"],
            "life": paths["life_fallback_model"],
        }

    metrics = {
        "power_dl": {
            "target": "powerconsumption",
            "backend": backend,
            **power_metrics,
        },
        "life_dl": {
            "target": "batterylife",
            "backend": backend,
            **life_metrics,
        },
    }

    with open(paths["metrics"], "w", encoding="utf-8") as metrics_file:
        json.dump(metrics, metrics_file, ensure_ascii=False, indent=2)

    timestamp = datetime.now()
    manifest = {
        "backend": backend,
        "version": timestamp.strftime("dl-%Y%m%d%H%M%S"),
        "updated_at": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "sequence_length": dataset["metadata"]["sequence_length"],
        "feature_columns": dataset["metadata"]["feature_columns"],
        "category_maps": dataset["metadata"]["category_maps"],
        "source_type": dataset["metadata"]["source_type"],
        "source_excel": dataset["metadata"].get("source_excel", ""),
        "sample_count": dataset["metadata"]["sample_count"],
        "model_paths": model_paths,
    }
    with open(paths["manifest"], "w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, ensure_ascii=False, indent=2)

    return {
        "metrics": metrics,
        "manifest": manifest,
        "dataset": dataset_result["metadata"],
        "paths": paths,
    }


def ensure_dl_artifacts(force_retrain=False, queryset_or_records=None, excel_path=None, base_dir=None):
    paths = get_dl_artifact_paths(base_dir)
    if force_retrain or not os.path.exists(paths["metrics"]) or not os.path.exists(paths["manifest"]):
        return train_dl_bundle(
            queryset_or_records=queryset_or_records,
            excel_path=excel_path,
            base_dir=base_dir,
            force_retrain=force_retrain,
        )
    return {
        "paths": paths,
    }


def load_dl_bundle(force_retrain=False, queryset_or_records=None, excel_path=None, base_dir=None):
    ensure_dl_artifacts(
        force_retrain=force_retrain,
        queryset_or_records=queryset_or_records,
        excel_path=excel_path,
        base_dir=base_dir,
    )
    paths = get_dl_artifact_paths(base_dir)
    with open(paths["metrics"], "r", encoding="utf-8") as metrics_file:
        metrics = json.load(metrics_file)
    with open(paths["manifest"], "r", encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)

    models = {}
    if manifest["backend"] == "pytorch_gru" and TORCH_AVAILABLE:  # pragma: no cover
        power_model = SequenceRegressor(input_size=len(manifest["feature_columns"]))
        power_model.load_state_dict(torch.load(manifest["model_paths"]["power"], map_location="cpu"))
        power_model.eval()
        life_model = SequenceRegressor(input_size=len(manifest["feature_columns"]))
        life_model.load_state_dict(torch.load(manifest["model_paths"]["life"], map_location="cpu"))
        life_model.eval()
        models["power"] = power_model
        models["life"] = life_model
    else:
        models["power"] = joblib.load(manifest["model_paths"]["power"])
        models["life"] = joblib.load(manifest["model_paths"]["life"])

    return {
        "models": models,
        "metrics": metrics,
        "manifest": manifest,
        "paths": paths,
    }


def _predict_with_loaded_bundle(payload, bundle):
    record = normalize_prediction_payload(payload)
    sequence = build_inference_sequence(record, bundle["manifest"])

    if bundle["manifest"]["backend"] == "pytorch_gru" and TORCH_AVAILABLE:  # pragma: no cover
        with torch.no_grad():
            power_value = float(bundle["models"]["power"](_torch_tensor(sequence)).cpu().numpy()[0])
            life_value = float(bundle["models"]["life"](_torch_tensor(sequence)).cpu().numpy()[0])
    else:
        flat_sequence = sequence.reshape(1, -1)
        power_value = float(bundle["models"]["power"].predict(flat_sequence)[0])
        life_value = float(bundle["models"]["life"].predict(flat_sequence)[0])

    predicted_power = round(max(power_value, 0.0), 2)
    predicted_life = max(int(round(life_value)), 1)
    risk_level = _infer_risk_level(predicted_power, predicted_life)
    major_factors = _build_major_factors(record, predicted_power, predicted_life)
    backend = bundle["manifest"]["backend"]
    model_name = "PyTorch GRU" if backend == "pytorch_gru" else "Sklearn MLP Fallback"

    return {
        "vehiclemodel": record["vehiclemodel"],
        "batterycapacity": int(round(record["batterycapacity"])),
        "accumulatedmileage": int(round(record["accumulatedmileage"])),
        "drivingbehaviorrating": int(round(record["drivingbehaviorrating"])),
        "batterylife": predicted_life,
        "predictedpowerconsumption": predicted_power,
        "risklevel": risk_level,
        "modelname": model_name,
        "modelversion": bundle["manifest"]["version"],
        "majorfactors": major_factors,
        "updated_at": bundle["manifest"]["updated_at"],
        "backend": backend,
        "trainingSource": bundle["manifest"]["source_type"],
        "metrics": bundle["metrics"],
    }


def predict_drivinglog_dl(payload, force_retrain=False, queryset_or_records=None, excel_path=None, base_dir=None):
    bundle = load_dl_bundle(
        force_retrain=force_retrain,
        queryset_or_records=queryset_or_records,
        excel_path=excel_path,
        base_dir=base_dir,
    )
    return _predict_with_loaded_bundle(payload, bundle)

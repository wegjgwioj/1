# coding:utf-8
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.io import loadmat


NASA_BATTERY_DATASET_NAME = "NASA PCoE Battery Aging"
NASA_BATTERY_DATASET_URL = "https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip"
DEFAULT_EOL_CAPACITY = 1.4


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, np.ndarray):
        return [item for item in value.reshape(-1)]
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _get_field(value, field_name, default=None):
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(field_name, default)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if isinstance(value, np.void) and value.dtype.names and field_name in value.dtype.names:
        return value[field_name]
    if isinstance(value, np.ndarray) and value.dtype.names and field_name in value.dtype.names:
        return value[field_name]
    return default


def _as_text(value):
    items = _as_list(value)
    if not items:
        return ""
    first = items[0]
    if isinstance(first, bytes):
        return first.decode("utf-8", errors="ignore")
    return str(first)


def _as_float(value, default=None):
    items = _as_list(value)
    if not items:
        return default
    try:
        return float(np.asarray(items[0]).reshape(-1)[0])
    except Exception:
        return default


def _mean(value):
    try:
        values = np.asarray(_as_list(value), dtype=float).reshape(-1)
        values = values[np.isfinite(values)]
        if len(values) == 0:
            return 0.0
        return float(values.mean())
    except Exception:
        return 0.0


def _duration_seconds(value):
    try:
        values = np.asarray(_as_list(value), dtype=float).reshape(-1)
        values = values[np.isfinite(values)]
        if len(values) == 0:
            return 0.0
        return float(values.max() - values.min())
    except Exception:
        return 0.0


def _root_variable(mat_payload):
    for key, value in mat_payload.items():
        if not key.startswith("__"):
            return key, value
    raise ValueError("未在 NASA .mat 文件中找到电池结构体变量。")


def parse_nasa_mat_file(mat_path):
    mat_payload = loadmat(str(mat_path), squeeze_me=True, struct_as_record=False)
    battery_id, root = _root_variable(mat_payload)
    cycles = _as_list(_get_field(root, "cycle", []))
    rows = []

    for cycle in cycles:
        cycle_type = _as_text(_get_field(cycle, "type", "")).lower()
        if cycle_type != "discharge":
            continue
        data = _get_field(cycle, "data", None)
        capacity = _as_float(_get_field(data, "Capacity", None))
        if capacity is None or capacity <= 0:
            continue
        discharge_index = len(rows) + 1
        rows.append(
            {
                "battery_id": battery_id,
                "cycle_index": discharge_index,
                "capacity": capacity,
                "voltage_mean": _mean(_get_field(data, "Voltage_measured", None)),
                "current_mean": _mean(_get_field(data, "Current_measured", None)),
                "temperature_mean": _mean(_get_field(data, "Temperature_measured", None)),
                "duration_seconds": _duration_seconds(_get_field(data, "Time", None)),
            }
        )
    return rows


def build_life_frame(rows, eol_capacity=DEFAULT_EOL_CAPACITY, min_valid_capacity=0.5):
    frame = pd.DataFrame(list(rows))
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "battery_id",
                "cycle_index",
                "capacity",
                "soh",
                "rul",
                "voltage_mean",
                "current_mean",
                "temperature_mean",
                "duration_seconds",
            ]
        )

    frame = frame.copy()
    frame["cycle_index"] = pd.to_numeric(frame["cycle_index"], errors="coerce")
    frame["capacity"] = pd.to_numeric(frame["capacity"], errors="coerce")
    frame = frame.dropna(subset=["battery_id", "cycle_index", "capacity"])
    frame = frame[frame["capacity"] > 0].sort_values(["battery_id", "cycle_index"]).reset_index(drop=True)
    frame = frame[frame["capacity"] >= float(min_valid_capacity)].reset_index(drop=True)
    output_parts = []

    for battery_id, group in frame.groupby("battery_id", dropna=False):
        group = group.sort_values("cycle_index").reset_index(drop=True).copy()
        # NASA 后续批次中可能出现非完整放电记录；用最大有效容量作为参考容量可避免 SOH 被异常首条记录放大。
        reference_capacity = float(group["capacity"].max())
        eol_rows = group[group["capacity"] <= float(eol_capacity)]
        if not eol_rows.empty:
            eol_cycle = int(eol_rows["cycle_index"].iloc[0])
        else:
            eol_cycle = int(group["cycle_index"].iloc[-1])
        group["soh"] = (group["capacity"] / reference_capacity).clip(lower=0, upper=1)
        group["rul"] = (eol_cycle - group["cycle_index"]).clip(lower=0).astype(int)
        output_parts.append(group)

    return pd.concat(output_parts, ignore_index=True)


def get_battery_life_artifact_paths(base_dir=None):
    root_dir = base_dir or os.getcwd()
    artifact_dir = os.path.join(root_dir, "artifacts", "battery_life")
    return {
        "artifact_dir": artifact_dir,
        "figure_dir": os.path.join(artifact_dir, "figures"),
        "dataset": os.path.join(artifact_dir, "nasa_life_dataset.csv"),
        "manifest": os.path.join(artifact_dir, "nasa_life_dataset_manifest.json"),
        "soh_model": os.path.join(artifact_dir, "nasa_soh_model.pkl"),
        "rul_model": os.path.join(artifact_dir, "nasa_rul_model.pkl"),
        "metrics": os.path.join(artifact_dir, "nasa_life_metrics.json"),
        "training_manifest": os.path.join(artifact_dir, "nasa_life_training_manifest.json"),
        "capacity_curve": os.path.join(artifact_dir, "figures", "nasa_capacity_degradation.png"),
        "soh_prediction_plot": os.path.join(artifact_dir, "figures", "nasa_soh_prediction.png"),
        "rul_prediction_plot": os.path.join(artifact_dir, "figures", "nasa_rul_prediction.png"),
    }


def download_nasa_zip(target_zip, url=NASA_BATTERY_DATASET_URL):
    os.makedirs(os.path.dirname(target_zip), exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(target_zip, "wb") as zip_file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    zip_file.write(chunk)
    return target_zip


def extract_nasa_zip(zip_path, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(target_dir)
    return target_dir


def extract_nested_zip_files(source_dir):
    source_path = Path(source_dir)
    processed = set()
    while True:
        zip_files = [path for path in source_path.rglob("*.zip") if str(path.resolve()) not in processed]
        if not zip_files:
            break
        for zip_file in zip_files:
            processed.add(str(zip_file.resolve()))
            target_dir = zip_file.with_suffix("")
            if find_nasa_mat_files(target_dir):
                continue
            try:
                extract_nasa_zip(str(zip_file), str(target_dir))
            except zipfile.BadZipFile:
                continue
    return source_dir


def find_nasa_mat_files(source_dir):
    source_path = Path(source_dir)
    if not source_path.exists():
        return []
    return sorted(
        path
        for path in source_path.rglob("*.mat")
        if path.name.lower().startswith("b") or path.stem.upper().startswith("B")
    )


def prepare_nasa_battery_dataset(
    source_dir,
    base_dir=None,
    download=False,
    url=NASA_BATTERY_DATASET_URL,
    eol_capacity=DEFAULT_EOL_CAPACITY,
    min_valid_capacity=0.5,
):
    source_path = Path(source_dir)
    if download and not find_nasa_mat_files(source_path):
        zip_path = source_path / "nasa_battery_dataset.zip"
        download_nasa_zip(str(zip_path), url=url)
        extract_nasa_zip(str(zip_path), str(source_path))
    if not find_nasa_mat_files(source_path):
        extract_nested_zip_files(source_path)

    rows = []
    for mat_file in find_nasa_mat_files(source_path):
        rows.extend(parse_nasa_mat_file(mat_file))

    frame = build_life_frame(rows, eol_capacity=eol_capacity, min_valid_capacity=min_valid_capacity)
    if frame.empty:
        raise ValueError("未解析到 NASA discharge 容量循环数据，请检查数据目录或下载是否完整。")

    paths = get_battery_life_artifact_paths(base_dir)
    os.makedirs(paths["artifact_dir"], exist_ok=True)
    frame.to_csv(paths["dataset"], index=False, encoding="utf-8-sig")
    manifest = {
        "dataset": NASA_BATTERY_DATASET_NAME,
        "source_url": url,
        "source_dir": str(source_path),
        "eol_capacity": float(eol_capacity),
        "min_valid_capacity": float(min_valid_capacity),
        "soh_reference": "max_valid_capacity_per_battery",
        "battery_count": int(frame["battery_id"].nunique()),
        "sample_count": int(len(frame)),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(paths["manifest"], "w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, ensure_ascii=False, indent=2)
    return {"frame": frame, "paths": paths, "manifest": manifest}


def load_nasa_battery_frame(base_dir=None):
    paths = get_battery_life_artifact_paths(base_dir)
    return pd.read_csv(paths["dataset"])

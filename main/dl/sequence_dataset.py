# coding:utf-8
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd

from main.excel_sources import load_raw_telemetry_records, resolve_default_raw_telemetry_excel
from main.ml.feature_engineering import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    build_training_dataframe,
)


SEQUENCE_DATASET_PATH = os.path.join("artifacts", "sequence", "drivinglog_sequence_dataset.npz")
SEQUENCE_META_PATH = os.path.join("artifacts", "sequence", "drivinglog_sequence_meta.json")


def _resolve_training_frame(queryset_or_records=None, excel_path=None):
    raw_records = load_raw_telemetry_records(excel_path=excel_path)
    if raw_records:
        frame = build_training_dataframe(raw_records)
        if not frame.empty and len(frame) >= 3:
            return frame, "raw_excel"

    if queryset_or_records is not None:
        frame = build_training_dataframe(queryset_or_records)
        if not frame.empty and len(frame) >= 3:
            return frame, "drivinglog_table"

    frame = build_training_dataframe(queryset_or_records or [])
    return frame, "drivinglog_table"


def _encode_sequence_frame(frame):
    encoded = frame.copy().reset_index(drop=True)
    category_maps = {}
    for column in CATEGORICAL_FEATURES:
        values = encoded[column].fillna("").astype(str)
        codes, uniques = pd.factorize(values, sort=True)
        category_maps[column] = {value: int(index + 1) for index, value in enumerate(uniques.tolist())}
        encoded[f"{column}_code"] = (codes + 1).astype(float)
    feature_columns = NUMERIC_FEATURES + [f"{column}_code" for column in CATEGORICAL_FEATURES]
    return encoded, category_maps, feature_columns


def _sort_group(group):
    sort_columns = [column for column in ("collectiontime", "starttime", "endtime", "accumulatedmileage") if column in group.columns]
    return group.sort_values(sort_columns).reset_index(drop=True)


def build_sequence_samples(frame, sequence_length=3):
    encoded, category_maps, feature_columns = _encode_sequence_frame(frame)
    sample_sequences = []
    power_targets = []
    life_targets = []

    for _, group in encoded.groupby("vehiclemodel", dropna=False):
        group = _sort_group(group)
        if len(group) < sequence_length:
            continue
        for end_index in range(sequence_length - 1, len(group)):
            window = group.iloc[end_index - sequence_length + 1 : end_index + 1]
            sample_sequences.append(window[feature_columns].to_numpy(dtype=np.float32))
            power_targets.append(float(window.iloc[-1]["powerconsumption"]))
            life_targets.append(float(window.iloc[-1]["batterylife"]))

    if not sample_sequences:
        for _, row in encoded.iterrows():
            base = row[feature_columns].to_numpy(dtype=np.float32)
            sample_sequences.append(np.repeat(base.reshape(1, -1), sequence_length, axis=0))
            power_targets.append(float(row["powerconsumption"]))
            life_targets.append(float(row["batterylife"]))

    return {
        "X": np.stack(sample_sequences).astype(np.float32),
        "y_power": np.asarray(power_targets, dtype=np.float32),
        "y_life": np.asarray(life_targets, dtype=np.float32),
        "feature_columns": feature_columns,
        "category_maps": category_maps,
    }


def get_sequence_artifact_paths(base_dir=None):
    root_dir = base_dir or os.getcwd()
    return {
        "sequence_dir": os.path.join(root_dir, "artifacts", "sequence"),
        "dataset": os.path.join(root_dir, SEQUENCE_DATASET_PATH),
        "meta": os.path.join(root_dir, SEQUENCE_META_PATH),
    }


def prepare_sequence_dataset(queryset_or_records=None, excel_path=None, base_dir=None, sequence_length=3):
    paths = get_sequence_artifact_paths(base_dir)
    os.makedirs(paths["sequence_dir"], exist_ok=True)

    default_excel = excel_path or resolve_default_raw_telemetry_excel(base_dir)
    frame, source_type = _resolve_training_frame(queryset_or_records=queryset_or_records, excel_path=default_excel)
    if frame.empty or len(frame) < 3:
        raise ValueError("可用于深度学习对比的有效样本不足，至少需要 3 条。")

    samples = build_sequence_samples(frame, sequence_length=sequence_length)
    np.savez(
        paths["dataset"],
        X=samples["X"],
        y_power=samples["y_power"],
        y_life=samples["y_life"],
    )

    metadata = {
        "source_type": source_type,
        "source_excel": default_excel if source_type == "raw_excel" else "",
        "sequence_length": sequence_length,
        "sample_count": int(samples["X"].shape[0]),
        "feature_columns": samples["feature_columns"],
        "category_maps": samples["category_maps"],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(paths["meta"], "w", encoding="utf-8") as meta_file:
        json.dump(metadata, meta_file, ensure_ascii=False, indent=2)

    return {
        "paths": paths,
        "metadata": metadata,
    }


def load_sequence_dataset(base_dir=None):
    paths = get_sequence_artifact_paths(base_dir)
    dataset = np.load(paths["dataset"])
    with open(paths["meta"], "r", encoding="utf-8") as meta_file:
        metadata = json.load(meta_file)
    return {
        "X": dataset["X"],
        "y_power": dataset["y_power"],
        "y_life": dataset["y_life"],
        "metadata": metadata,
        "paths": paths,
    }


def build_inference_sequence(payload, metadata):
    record = payload.copy()
    feature_row = []
    for column in NUMERIC_FEATURES:
        feature_row.append(float(record.get(column, 0)))
    for column in CATEGORICAL_FEATURES:
        mapping = metadata.get("category_maps", {}).get(column, {})
        encoded = mapping.get(str(record.get(column, "")), 0)
        feature_row.append(float(encoded))

    base = np.asarray(feature_row, dtype=np.float32)
    sequence_length = int(metadata.get("sequence_length", 3))
    return np.repeat(base.reshape(1, -1), sequence_length, axis=0).reshape(1, sequence_length, -1)

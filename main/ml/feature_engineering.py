# coding:utf-8
import os

import pandas as pd

from main.excel_sources import load_raw_telemetry_records, resolve_default_raw_telemetry_excel
from .data_cleaning import summarize_drivinglog_quality


NUMERIC_FEATURES = [
    "batterycapacity",
    "accumulatedmileage",
    "averagespeed",
    "batterylevel",
    "rapidaccelerationtimes",
    "numberofrapiddecelerations",
    "numberofspeedingincidents",
    "drivingbehaviorrating",
]

CATEGORICAL_FEATURES = [
    "vehiclemodel",
    "drivingroute",
]

TARGET_COLUMNS = {
    "power": "powerconsumption",
    "life": "batterylife",
}

NUMERIC_DEFAULTS = {
    "batterycapacity": 70,
    "accumulatedmileage": 120,
    "averagespeed": 55,
    "batterylevel": 60,
    "rapidaccelerationtimes": 1,
    "numberofrapiddecelerations": 1,
    "numberofspeedingincidents": 0,
    "drivingbehaviorrating": 75,
}


def fill_missing_targets(frame):
    numeric_medians = frame.median(numeric_only=True)

    def fill_numeric(column, fallback):
        median = numeric_medians.get(column)
        if pd.isna(median):
            median = fallback
        return frame[column].fillna(median)

    battery_capacity = fill_numeric("batterycapacity", 70).clip(lower=1)
    accumulated_mileage = fill_numeric("accumulatedmileage", 120)
    average_speed = fill_numeric("averagespeed", 55)
    battery_level = fill_numeric("batterylevel", 60).clip(lower=0, upper=100)
    rapid_acceleration_times = fill_numeric("rapidaccelerationtimes", 1)
    rapid_deceleration_times = fill_numeric("numberofrapiddecelerations", 1)
    speeding_times = fill_numeric("numberofspeedingincidents", 0)
    behavior_rating = fill_numeric("drivingbehaviorrating", 75).clip(lower=0, upper=100)

    estimated_power = (
        10
        + (100 - behavior_rating) * 0.05
        + (average_speed - 45).clip(lower=0) * 0.04
        + rapid_acceleration_times * 0.35
        + rapid_deceleration_times * 0.2
        + speeding_times * 0.5
        + (accumulated_mileage / battery_capacity) * 0.08
        + (100 - battery_level) * 0.015
    ).clip(lower=8, upper=35)

    estimated_life = (
        84
        + battery_capacity * 0.22
        - accumulated_mileage * 0.05
        + behavior_rating * 0.12
        - rapid_acceleration_times * 0.35
        - speeding_times * 0.45
    ).clip(lower=12, upper=120)

    frame["powerconsumption"] = frame["powerconsumption"].where(
        frame["powerconsumption"].notna(),
        estimated_power.round(2),
    )
    frame["batterylife"] = frame["batterylife"].where(
        frame["batterylife"].notna(),
        estimated_life.round().astype(int),
    )
    return frame


def _finalize_training_frame(frame):
    if frame.empty:
        return frame

    for column in NUMERIC_FEATURES + list(TARGET_COLUMNS.values()):
        if column not in frame.columns:
            frame[column] = None
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if column in NUMERIC_DEFAULTS and frame[column].isna().all():
            frame[column] = NUMERIC_DEFAULTS[column]

    for column in CATEGORICAL_FEATURES:
        if column not in frame.columns:
            frame[column] = ""
        frame[column] = frame[column].fillna("").astype(str)

    frame = fill_missing_targets(frame)
    frame = frame.dropna(subset=["batterycapacity", "accumulatedmileage", "drivingbehaviorrating"])
    return frame


def build_training_dataframe(queryset_or_records=None, excel_path=None):
    if excel_path:
        frame = pd.DataFrame(load_raw_telemetry_records(excel_path=excel_path))
    else:
        summary = summarize_drivinglog_quality(queryset_or_records or [])
        frame = pd.DataFrame(summary["valid_rows"])
    return _finalize_training_frame(frame)


def resolve_training_dataframe(queryset_or_records=None, excel_path=None, source="auto"):
    default_excel = excel_path or resolve_default_raw_telemetry_excel()

    if source == "excel":
        frame = build_training_dataframe(excel_path=default_excel)
        return frame, {
            "source_type": "raw_excel",
            "source_excel": default_excel,
            "sample_count": int(len(frame)),
        }

    if source == "table":
        frame = build_training_dataframe(queryset_or_records=queryset_or_records)
        return frame, {
            "source_type": "drivinglog_table",
            "source_excel": "",
            "sample_count": int(len(frame)),
        }

    if default_excel and os.path.exists(default_excel):
        frame = build_training_dataframe(excel_path=default_excel)
        if not frame.empty and len(frame) >= 3:
            return frame, {
                "source_type": "raw_excel",
                "source_excel": default_excel,
                "sample_count": int(len(frame)),
            }

    frame = build_training_dataframe(queryset_or_records=queryset_or_records)
    return frame, {
        "source_type": "drivinglog_table",
        "source_excel": "",
        "sample_count": int(len(frame)),
    }


def get_feature_columns():
    return {
        "numeric": NUMERIC_FEATURES,
        "categorical": CATEGORICAL_FEATURES,
    }

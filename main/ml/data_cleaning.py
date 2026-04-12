# coding:utf-8
import json
import os
from collections import Counter
from datetime import datetime

from django.forms import model_to_dict


QUALITY_FIELDS = [
    "id",
    "vehiclenumber",
    "vehiclemodel",
    "batterycapacity",
    "batterylife",
    "accumulatedmileage",
    "starttime",
    "endtime",
    "averagespeed",
    "batterylevel",
    "powerconsumption",
    "drivingroute",
    "collectiontime",
    "rapidaccelerationtimes",
    "numberofrapiddecelerations",
    "numberofspeedingincidents",
    "energysavingsuggestions",
    "drivingbehaviorrating",
]


def _safe_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_datetime(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _serialize_value(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def _to_record(item):
    if isinstance(item, dict):
        return {key: _serialize_value(value) for key, value in item.items()}
    return {key: _serialize_value(value) for key, value in model_to_dict(item).items()}


def _iter_records(queryset_or_records):
    if hasattr(queryset_or_records, "values"):
        for item in queryset_or_records.values(*QUALITY_FIELDS):
            yield _to_record(item)
        return

    for item in queryset_or_records:
        record = _to_record(item)
        yield {key: record.get(key) for key in QUALITY_FIELDS}


def collect_record_issues(record):
    issues = []
    required_fields = ("vehiclenumber", "vehiclemodel", "batterycapacity", "batterylife", "accumulatedmileage")
    if any(record.get(field) in (None, "") for field in required_fields):
        issues.append("missing_required")

    batterycapacity = _safe_float(record.get("batterycapacity"))
    if batterycapacity is not None and batterycapacity <= 0:
        issues.append("invalid_batterycapacity")

    batterylevel = _safe_float(record.get("batterylevel"))
    if batterylevel is not None and (batterylevel < 0 or batterylevel > 100):
        issues.append("invalid_batterylevel")

    accumulatedmileage = _safe_float(record.get("accumulatedmileage"))
    if accumulatedmileage is not None and accumulatedmileage < 0:
        issues.append("negative_accumulatedmileage")

    powerconsumption = _safe_float(record.get("powerconsumption"))
    if powerconsumption is not None and powerconsumption < 0:
        issues.append("negative_powerconsumption")

    averagespeed = _safe_float(record.get("averagespeed"))
    if averagespeed is not None and (averagespeed < 0 or averagespeed > 220):
        issues.append("invalid_averagespeed")

    starttime = _safe_datetime(record.get("starttime"))
    endtime = _safe_datetime(record.get("endtime"))
    if record.get("starttime") not in (None, "") and starttime is None:
        issues.append("invalid_starttime")
    if record.get("endtime") not in (None, "") and endtime is None:
        issues.append("invalid_endtime")
    if starttime and endtime and starttime > endtime:
        issues.append("time_order_error")

    return issues


def summarize_drivinglog_quality(queryset_or_records):
    issues_counter = Counter()
    valid_rows = []
    invalid_rows = []

    for record in _iter_records(queryset_or_records):
        issues = collect_record_issues(record)
        if issues:
            issues_counter.update(issues)
            invalid_rows.append(
                {
                    "id": record.get("id"),
                    "vehiclenumber": record.get("vehiclenumber"),
                    "vehiclemodel": record.get("vehiclemodel"),
                    "issues": issues,
                }
            )
        else:
            valid_rows.append(record)

    return {
        "total_count": len(valid_rows) + len(invalid_rows),
        "valid_count": len(valid_rows),
        "invalid_count": len(invalid_rows),
        "issues": dict(issues_counter),
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
    }


def export_cleanse_artifacts(summary, base_dir):
    os.makedirs(base_dir, exist_ok=True)
    report_path = os.path.join(base_dir, "drivinglog_cleanse_report.json")
    training_path = os.path.join(base_dir, "drivinglog_training_rows.json")

    with open(report_path, "w", encoding="utf-8") as report_file:
        json.dump(
            {
                "total_count": summary["total_count"],
                "valid_count": summary["valid_count"],
                "invalid_count": summary["invalid_count"],
                "issues": summary["issues"],
                "invalid_rows": summary["invalid_rows"],
            },
            report_file,
            ensure_ascii=False,
            indent=2,
        )

    with open(training_path, "w", encoding="utf-8") as training_file:
        json.dump(summary["valid_rows"], training_file, ensure_ascii=False, indent=2)

    return {
        "report_path": report_path,
        "training_path": training_path,
    }

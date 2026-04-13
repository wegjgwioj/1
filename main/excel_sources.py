# coding:utf-8
import os
import re
from datetime import datetime

import xlrd


RAW_TELEMETRY_EXCEL = os.path.join("docs", "待提交", "新数据21507条【备份】.xlsx")
SUMMARY_DISPLAY_EXCEL = os.path.join("docs", "待提交", "数据2.xlsx")


def resolve_default_raw_telemetry_excel(base_dir=None):
    root_dir = base_dir or os.getcwd()
    return os.path.join(root_dir, RAW_TELEMETRY_EXCEL)


def resolve_default_summary_display_excel(base_dir=None):
    root_dir = base_dir or os.getcwd()
    return os.path.join(root_dir, SUMMARY_DISPLAY_EXCEL)


def _safe_float(value, default=0.0):
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    return int(round(_safe_float(value, default)))


def _clip(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def _parse_numeric_list(value):
    if value in (None, ""):
        return []
    if isinstance(value, (list, tuple)):
        return [float(item) for item in value if str(item).strip() != ""]
    numbers = re.findall(r"-?\d+(?:\.\d+)?", str(value))
    return [float(item) for item in numbers]


def _mean_or_default(values, default=0.0):
    if not values:
        return default
    return float(sum(values) / len(values))


def _normalize_time_text(value):
    if value in (None, ""):
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, (int, float)):
        return ""
    text = str(value).strip()
    if len(text) == 14 and text.isdigit():
        try:
            return datetime.strptime(text, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return text
    if len(text) == 8 and text.isdigit():
        try:
            return datetime.strptime(text, "%Y%m%d").strftime("%Y-%m-%d 00:00:00")
        except ValueError:
            return text
    return text


def _derive_behavior_features(speed_values, total_current):
    rapid_acceleration = 0
    rapid_deceleration = 0
    speeding = 0
    for index, speed in enumerate(speed_values):
        if speed > 100:
            speeding += 1
        if index == 0:
            continue
        delta = speed - speed_values[index - 1]
        if delta >= 10:
            rapid_acceleration += 1
        elif delta <= -10:
            rapid_deceleration += 1

    penalty = (
        rapid_acceleration * 3.5
        + rapid_deceleration * 2.5
        + speeding * 6
        + max(abs(total_current) - 80, 0) * 0.08
    )
    rating = int(round(_clip(100 - penalty, 35, 98)))
    return rapid_acceleration, rapid_deceleration, speeding, rating


def build_raw_telemetry_record(row):
    start_mileage = _safe_float(row.get("conditionStartMileage"))
    end_mileage = _safe_float(row.get("conditionEndMileage") or row.get("segmentEndMileage"))
    distance = max(end_mileage - start_mileage, 0.0)
    start_soc = _safe_float(row.get("conditionStartSoc") or row.get("segmentStartSoc"), default=60.0)
    end_soc = _safe_float(row.get("conditionEndSoc") or row.get("segmentEndSoc"), default=start_soc)
    soc_drop = max(start_soc - end_soc, 0.0)
    total_current = _safe_float(row.get("totalCurrentMean"))
    max_temp = _safe_float(row.get("maxTempMean") or row.get("tempListMean"), default=28.0)

    speed_values = _parse_numeric_list(row.get("speedList"))
    average_speed = _mean_or_default(speed_values, default=max(distance, 30.0))
    rapid_acceleration, rapid_deceleration, speeding, behavior_rating = _derive_behavior_features(
        speed_values,
        total_current,
    )

    energy_consume = _safe_float(row.get("energyConsume"))
    power_mean = abs(_safe_float(row.get("powerMean")))
    if energy_consume <= 0:
        energy_consume = 0.18 * distance + 0.12 * soc_drop + power_mean * 0.03
    power_consumption = round(_clip(energy_consume, 8.0, 35.0), 2)

    battery_capacity = 75.0
    if soc_drop > 0:
        battery_capacity = _clip(power_consumption / max(soc_drop / 100.0, 0.08), 45.0, 120.0)

    life_proxy = 96 + battery_capacity * 0.08 - end_mileage * 0.025 - max_temp * 0.45 - abs(total_current) * 0.03
    life_proxy += end_soc * 0.18 + behavior_rating * 0.08
    batterylife = int(round(_clip(life_proxy, 12, 120)))

    start_time = _normalize_time_text(
        row.get("conditionStartDateStr") or row.get("segmentStartDateStr") or row.get("pdate")
    )
    end_time = _normalize_time_text(
        row.get("conditionEndDateStr") or row.get("segmentEndDateStr") or start_time
    )

    return {
        "vehiclenumber": f"VID-{row.get('vid') or 'UNKNOWN'}",
        "vehiclemodel": str(row.get("vid") or "原始车型"),
        "batterycapacity": int(round(battery_capacity)),
        "batterylife": batterylife,
        "accumulatedmileage": int(round(max(end_mileage, distance))),
        "starttime": start_time,
        "endtime": end_time,
        "averagespeed": int(round(_clip(average_speed, 0, 160))),
        "batterylevel": int(round(_clip(end_soc, 0, 100))),
        "powerconsumption": power_consumption,
        "drivingroute": str(row.get("segmentType") or "原始工况"),
        "collectiontime": row.get("pdate") or end_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rapidaccelerationtimes": rapid_acceleration,
        "numberofrapiddecelerations": rapid_deceleration,
        "numberofspeedingincidents": speeding,
        "energysavingsuggestions": "原始时序推断",
        "drivingbehaviorrating": behavior_rating,
    }


def load_raw_telemetry_records(excel_path=None, base_dir=None):
    path = excel_path or resolve_default_raw_telemetry_excel(base_dir)
    if not path or not os.path.exists(path):
        return []

    book = xlrd.open_workbook(path)
    sheet = book.sheet_by_index(0)
    headers = [str(sheet.cell_value(0, col)).strip() for col in range(sheet.ncols)]
    records = []
    for row_index in range(1, sheet.nrows):
        row = {headers[col]: sheet.cell_value(row_index, col) for col in range(sheet.ncols)}
        try:
            records.append(build_raw_telemetry_record(row))
        except Exception:
            continue
    return records


def _excel_datetime(value, datemode):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            return xlrd.xldate.xldate_as_datetime(value, datemode)
        except Exception:
            return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def load_summary_display_records(excel_path=None, base_dir=None):
    path = excel_path or resolve_default_summary_display_excel(base_dir)
    if not path or not os.path.exists(path):
        return []

    book = xlrd.open_workbook(path)
    sheet = book.sheet_by_index(0)
    headers = [str(sheet.cell_value(0, col)).strip() for col in range(sheet.ncols)]
    index_map = {header: idx for idx, header in enumerate(headers)}

    def cell(row_index, header, default=None):
        col_index = index_map.get(header)
        if col_index is None:
            return default
        value = sheet.cell_value(row_index, col_index)
        return default if value == "" else value

    records = []
    for row_index in range(1, sheet.nrows):
        records.append(
            {
                "vehiclenumber": str(cell(row_index, "车辆编号", "")).strip(),
                "vehiclemodel": str(cell(row_index, "车辆型号", "")).strip(),
                "batterycapacity": _safe_int(cell(row_index, "电池容量")),
                "batterylife": _safe_int(cell(row_index, "电池寿命按月算数字格式")),
                "accumulatedmileage": _safe_int(cell(row_index, "行驶里程")),
                "starttime": _excel_datetime(cell(row_index, "开始时间"), book.datemode),
                "endtime": _excel_datetime(cell(row_index, "结束时间"), book.datemode),
                "averagespeed": _safe_int(cell(row_index, "平均车速")),
                "batterylevel": _safe_int(cell(row_index, "电池余量")),
                "powerconsumption": _safe_int(cell(row_index, "耗电量")),
                "drivingroute": str(cell(row_index, "行驶路线", "")).strip(),
                "collectiontime": _excel_datetime(cell(row_index, "采集时间"), book.datemode),
                "rapidaccelerationtimes": _safe_int(cell(row_index, "急加速次数")),
                "numberofrapiddecelerations": _safe_int(cell(row_index, "急减速次数")),
                "numberofspeedingincidents": _safe_int(cell(row_index, "超速次数")),
                "energysavingsuggestions": str(cell(row_index, "节能建议", "")).strip(),
                "drivingbehaviorrating": _safe_int(cell(row_index, "驾驶行为评分")),
            }
        )
    return records

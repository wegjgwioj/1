# coding:utf-8
import json
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from main.excel_sources import load_summary_display_records
from main.models import drivinglog


def _normalize_datetime(value):
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


class Command(BaseCommand):
    help = "使用 数据2.xlsx 重建 drivinglog 展示表"

    def add_arguments(self, parser):
        parser.add_argument(
            "--excel-path",
            default="",
            help="指定汇总展示 Excel 路径，默认读取 docs/待提交/数据2.xlsx",
        )

    def handle(self, *args, **options):
        excel_path = options.get("excel_path") or None
        records = load_summary_display_records(excel_path=excel_path)
        if not records:
            raise ValueError("未读取到可用的汇总展示数据。")

        objects = []
        for record in records:
            payload = record.copy()
            payload["starttime"] = _normalize_datetime(payload.get("starttime"))
            payload["endtime"] = _normalize_datetime(payload.get("endtime"))
            payload["collectiontime"] = _normalize_datetime(payload.get("collectiontime"))
            payload["clicknum"] = 0
            payload["storeupnum"] = 0
            payload["discussnum"] = 0
            payload["clicktime"] = None
            objects.append(drivinglog(**payload))

        with transaction.atomic():
            drivinglog.objects.all().delete()
            drivinglog.objects.bulk_create(objects, batch_size=500)

        self.stdout.write(
            json.dumps(
                {
                    "count": len(objects),
                    "message": "drivinglog 展示表已按汇总 Excel 重建",
                },
                ensure_ascii=False,
                indent=2,
            )
        )

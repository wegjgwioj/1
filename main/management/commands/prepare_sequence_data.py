# coding:utf-8
import json

from django.core.management.base import BaseCommand

from main.dl import prepare_sequence_dataset
from main.models import drivinglog


class Command(BaseCommand):
    help = "构造深度学习对比所需的序列数据集"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=["auto", "table", "excel"],
            default="auto",
            help="指定序列数据构造来源：auto=优先业务表，不足时回退 Excel；table=仅业务表；excel=仅原始 Excel",
        )
        parser.add_argument(
            "--excel-path",
            default="",
            help="当 source=excel 或 auto 时，可手动指定原始 Excel 路径",
        )

    def handle(self, *args, **options):
        source = options.get("source", "auto")
        excel_path = options.get("excel_path") or None
        queryset_or_records = drivinglog.objects.all() if source in ("auto", "table") else None
        if source == "table":
            excel_path = None

        result = prepare_sequence_dataset(
            queryset_or_records=queryset_or_records,
            excel_path=excel_path,
        )
        self.stdout.write(json.dumps(result["metadata"], ensure_ascii=False, indent=2))

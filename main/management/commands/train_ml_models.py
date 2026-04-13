import json
import os

from django.core.management.base import BaseCommand

from main.ml.trainers import save_ml_artifacts, train_ml_bundle, train_neural_baseline_bundle
from main.models import drivinglog


class Command(BaseCommand):
    help = "训练行车日志机器学习模型并生成模型文件与指标报告"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=["auto", "table", "excel"],
            default="auto",
            help="指定训练来源：auto=优先原始遥测 Excel；table=仅业务展示表；excel=仅原始遥测 Excel",
        )
        parser.add_argument(
            "--excel-path",
            default="",
            help="指定原始遥测 Excel 路径",
        )

    def handle(self, *args, **options):
        source = options.get("source", "auto")
        excel_path = options.get("excel_path") or None
        queryset_or_records = drivinglog.objects.all() if source in ("auto", "table") else None
        if source == "table":
            excel_path = None

        models, metrics, source_info = train_ml_bundle(
            queryset_or_records=queryset_or_records,
            excel_path=excel_path,
            source=source,
        )
        comparison_models, comparison_metrics, _ = train_neural_baseline_bundle(
            queryset_or_records=queryset_or_records,
            excel_path=excel_path,
            source=source,
        )
        paths = save_ml_artifacts(
            models,
            metrics,
            os.getcwd(),
            comparison_models=comparison_models,
            comparison_metrics=comparison_metrics,
            manifest=source_info,
        )
        payload = {
            "metrics": metrics,
            "comparison_metrics": comparison_metrics,
            "artifacts": paths,
            "source": source_info,
        }
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))

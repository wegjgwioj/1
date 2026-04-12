import json
import os

from django.core.management.base import BaseCommand

from main.ml.data_cleaning import export_cleanse_artifacts, summarize_drivinglog_quality
from main.models import drivinglog


class Command(BaseCommand):
    help = "分析行车日志数据质量，并导出清洗报告与可训练记录"

    def handle(self, *args, **options):
        summary = summarize_drivinglog_quality(drivinglog.objects.all())
        base_dir = os.path.join(os.getcwd(), "artifacts", "reports")
        paths = export_cleanse_artifacts(summary, base_dir)
        payload = {
            "total_count": summary["total_count"],
            "valid_count": summary["valid_count"],
            "invalid_count": summary["invalid_count"],
            "issues": summary["issues"],
            "report_path": paths["report_path"],
            "training_path": paths["training_path"],
        }
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))

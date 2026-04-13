# coding:utf-8
import json

from django.core.management.base import BaseCommand

from main.dl import TORCH_AVAILABLE, get_dl_artifact_paths, load_dl_bundle
from main.ml.predictors import load_ml_bundle
from main.models import drivinglog


class Command(BaseCommand):
    help = "输出机器学习与深度学习对比实验报告"

    def handle(self, *args, **options):
        ml_bundle = load_ml_bundle(queryset=drivinglog.objects.all())
        dl_bundle = load_dl_bundle(queryset_or_records=drivinglog.objects.all())

        report = {
            "ml": {
                "version": ml_bundle["version"],
                "metrics": ml_bundle["metrics"],
                "comparison_metrics": ml_bundle.get("comparison_metrics", {}),
            },
            "dl": {
                "version": dl_bundle["manifest"]["version"],
                "backend": dl_bundle["manifest"]["backend"],
                "torch_available": TORCH_AVAILABLE,
                "metrics": dl_bundle["metrics"],
                "source_type": dl_bundle["manifest"]["source_type"],
            },
        }

        compare_path = get_dl_artifact_paths()["compare"]
        with open(compare_path, "w", encoding="utf-8") as compare_file:
            json.dump(report, compare_file, ensure_ascii=False, indent=2)

        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))

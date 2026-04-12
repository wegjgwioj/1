import json
import os

from django.core.management.base import BaseCommand

from main.ml.trainers import save_ml_artifacts, train_ml_bundle, train_neural_baseline_bundle
from main.models import drivinglog


class Command(BaseCommand):
    help = "训练行车日志机器学习模型并生成模型文件与指标报告"

    def handle(self, *args, **options):
        models, metrics = train_ml_bundle(drivinglog.objects.all())
        comparison_models, comparison_metrics = train_neural_baseline_bundle(drivinglog.objects.all())
        paths = save_ml_artifacts(
            models,
            metrics,
            os.getcwd(),
            comparison_models=comparison_models,
            comparison_metrics=comparison_metrics,
        )
        payload = {
            "metrics": metrics,
            "comparison_metrics": comparison_metrics,
            "artifacts": paths,
        }
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))

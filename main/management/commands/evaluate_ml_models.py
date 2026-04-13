import json
import os

from django.core.management.base import BaseCommand, CommandError

from main.ml.trainers import save_ml_artifacts, train_ml_bundle, train_neural_baseline_bundle
from main.models import drivinglog


class Command(BaseCommand):
    help = "输出当前机器学习模型评估指标"

    def handle(self, *args, **options):
        metrics_path = os.path.join(os.getcwd(), "artifacts", "reports", "ml_metrics.json")
        comparison_metrics_path = os.path.join(os.getcwd(), "artifacts", "reports", "ml_comparison_metrics.json")
        if not os.path.exists(metrics_path):
            try:
                models, metrics, source_info = train_ml_bundle(drivinglog.objects.all())
                comparison_models, comparison_metrics, _ = train_neural_baseline_bundle(drivinglog.objects.all())
            except ValueError as exc:
                raise CommandError(str(exc))
            save_ml_artifacts(
                models,
                metrics,
                os.getcwd(),
                comparison_models=comparison_models,
                comparison_metrics=comparison_metrics,
                manifest=source_info,
            )

        with open(metrics_path, "r", encoding="utf-8") as metrics_file:
            metrics = json.load(metrics_file)

        for model_name, result in metrics.items():
            self.stdout.write(f"[{model_name}]")
            self.stdout.write(f"MAE: {result['MAE']:.4f}")
            self.stdout.write(f"RMSE: {result['RMSE']:.4f}")
            self.stdout.write(f"R2: {result['R2']:.4f}")
        if os.path.exists(comparison_metrics_path):
            with open(comparison_metrics_path, "r", encoding="utf-8") as metrics_file:
                comparison_metrics = json.load(metrics_file)
            for model_name, result in comparison_metrics.items():
                self.stdout.write(f"[{model_name}]")
                self.stdout.write(f"MAE: {result['MAE']:.4f}")
                self.stdout.write(f"RMSE: {result['RMSE']:.4f}")
                self.stdout.write(f"R2: {result['R2']:.4f}")

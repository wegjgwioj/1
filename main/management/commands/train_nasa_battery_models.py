# coding:utf-8
import json

from django.core.management.base import BaseCommand

from main.battery_life import load_nasa_battery_frame
from main.battery_life.trainers import train_real_life_models


class Command(BaseCommand):
    help = "训练 NASA 真实电池寿命 SOH/RUL 模型并输出指标报告"

    def handle(self, *args, **options):
        frame = load_nasa_battery_frame()
        result = train_real_life_models(frame)
        payload = {
            "manifest": result["manifest"],
            "metrics": result["metrics"],
            "artifacts": result["paths"],
        }
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))

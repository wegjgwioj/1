# coding:utf-8
import json
import os

from django.core.management.base import BaseCommand

from main.battery_life import NASA_BATTERY_DATASET_URL, prepare_nasa_battery_dataset


class Command(BaseCommand):
    help = "解析 NASA PCoE Battery Aging 数据集，生成真实 SOH/RUL 寿命实验数据表"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-dir",
            default=os.path.join("datasets", "nasa_battery"),
            help="NASA 数据集解压目录；配合 --download 时也是下载与解压目录",
        )
        parser.add_argument("--download", action="store_true", help="当目录内无 .mat 文件时自动下载 NASA zip 数据集")
        parser.add_argument("--url", default=NASA_BATTERY_DATASET_URL, help="NASA Battery zip 下载地址")
        parser.add_argument("--eol-capacity", type=float, default=1.4, help="EOL 容量阈值，NASA 常用 1.4Ah")
        parser.add_argument("--min-valid-capacity", type=float, default=0.5, help="过滤非完整放电/异常容量记录的最小容量阈值")

    def handle(self, *args, **options):
        result = prepare_nasa_battery_dataset(
            source_dir=options["source_dir"],
            download=options["download"],
            url=options["url"],
            eol_capacity=options["eol_capacity"],
            min_valid_capacity=options["min_valid_capacity"],
        )
        payload = {
            "manifest": result["manifest"],
            "dataset_path": result["paths"]["dataset"],
        }
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))

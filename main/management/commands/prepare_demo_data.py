from django.core.management.base import BaseCommand

from util.demo_data import prepare_demo_data


class Command(BaseCommand):
    help = "整理答辩演示数据，标准化车型名称并清空旧车型知识库结果"

    def handle(self, *args, **options):
        stats = prepare_demo_data()
        self.stdout.write(self.style.SUCCESS("标准化车型名称 %s 条" % stats["updated_models"]))
        self.stdout.write(self.style.SUCCESS("标准化车辆编号 %s 条" % stats["updated_numbers"]))
        self.stdout.write(self.style.SUCCESS("清空车型知识记录 %s 条" % stats["deleted_knowledge"]))

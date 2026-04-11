from django.core.management.base import BaseCommand

from util.feature_schema import sync_feature_schema


class Command(BaseCommand):
    help = "同步收藏、评论、车型知识等补丁表结构到当前数据库"

    def handle(self, *args, **options):
        actions = sync_feature_schema()
        if not actions:
            self.stdout.write("feature schema already up to date")
            return

        for action in actions:
            self.stdout.write(self.style.SUCCESS(action))

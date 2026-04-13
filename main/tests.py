# coding:utf-8
import base64
import io
import json
import os
from importlib import import_module
from unittest.mock import Mock, patch

from django.apps import apps
from django.core.management import call_command
from django.db import connection
from django.test import Client, TestCase, TransactionTestCase

from dj2.settings import dbName as schemaName
from .models import drivinglog, user, users


class BaseApiTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.front_user = user.objects.create(
            useraccount="test_user",
            password="123456",
            username="测试用户",
            gender="男",
            mobilephone="13800000000",
        )
        self.admin_user = users.objects.create(
            username="admin_test",
            password="123456",
            role="管理员",
            image="",
        )
        self.log_a = drivinglog.objects.create(
            vehiclenumber="CAR-001",
            vehiclemodel="Model-A",
            batterycapacity=90,
            batterylife=40,
            accumulatedmileage=120,
            drivingroute="机场-酒店高速干线",
            drivingbehaviorrating=88,
        )
        self.log_b = drivinglog.objects.create(
            vehiclenumber="CAR-002",
            vehiclemodel="Model-A",
            batterycapacity=85,
            batterylife=36,
            accumulatedmileage=180,
            drivingroute="机场-酒店高速干线",
            drivingbehaviorrating=80,
        )
        self.log_c = drivinglog.objects.create(
            vehiclenumber="CAR-003",
            vehiclemodel="Model-B",
            batterycapacity=100,
            batterylife=55,
            accumulatedmileage=260,
            drivingroute="东站-西站山区道路",
            drivingbehaviorrating=60,
        )

    def api(self, suffix):
        return f"/{schemaName}/{suffix}"

    def token(self, table_name="user", params=None):
        payload = {"tablename": table_name, "params": params or {"id": self.front_user.id}}
        return base64.b64encode(str(payload).encode("utf-8")).decode("utf-8")

    def auth_headers(self, table_name="user", params=None):
        return {"HTTP_TOKEN": self.token(table_name=table_name, params=params)}

    def get_model_or_fail(self, model_name):
        try:
            return apps.get_model("main", model_name)
        except LookupError:
            self.fail(f"模型 {model_name} 尚未实现")


class ModelSmokeTest(BaseApiTestCase):
    def test_models_and_fields_exist_for_feature_patch(self):
        model_names = {model.__name__.lower() for model in apps.get_app_config("main").get_models()}
        self.assertIn("storeup", model_names)
        self.assertIn("discussdrivinglog", model_names)
        self.assertIn("vehicleknowledge", model_names)

        drivinglog_fields = {field.name for field in drivinglog._meta.fields}
        self.assertIn("storeupnum", drivinglog_fields)
        self.assertIn("discussnum", drivinglog_fields)

        VehicleKnowledge = self.get_model_or_fail("vehicleknowledge")
        knowledge_fields = {field.name for field in VehicleKnowledge._meta.fields}
        self.assertIn("vehiclemodel", knowledge_fields)
        self.assertIn("summary", knowledge_fields)
        self.assertIn("crawlstatus", knowledge_fields)


class VehicleKnowledgeParserTest(TestCase):
    def test_extract_vehicle_knowledge_from_baike_like_html(self):
        module = import_module("util.vehicle_knowledge_crawler")
        html = """
        <html>
          <body>
            <div class="lemmaSummary_O3o_W J-summary">
              比亚迪海豹是比亚迪推出的纯电动轿车，主打高续航与智能化配置。
            </div>
            <div class="basic-info J-basic-info">
              <dl>
                <dt class="basicInfo-item name">所属品牌</dt>
                <dd class="basicInfo-item value">比亚迪</dd>
                <dt class="basicInfo-item name">电池类型</dt>
                <dd class="basicInfo-item value">磷酸铁锂电池</dd>
                <dt class="basicInfo-item name">CLTC纯电续航</dt>
                <dd class="basicInfo-item value">700km</dd>
                <dt class="basicInfo-item name">快充时间</dt>
                <dd class="basicInfo-item value">0.5小时</dd>
              </dl>
            </div>
          </body>
        </html>
        """

        result = module.extract_vehicle_knowledge(
            html_string=html,
            vehiclemodel="比亚迪海豹",
            sourceurl="https://baike.baidu.com/item/比亚迪海豹",
        )

        self.assertEqual(result["vehiclemodel"], "比亚迪海豹")
        self.assertIn("纯电动轿车", result["summary"])
        self.assertEqual(result["manufacturer"], "比亚迪")
        self.assertEqual(result["batterytype"], "磷酸铁锂电池")
        self.assertEqual(result["officialrange"], "700km")
        self.assertEqual(result["chargeinfo"], "0.5小时")


class VehicleKnowledgeCrawlFlowTest(BaseApiTestCase):
    def _mock_response(self, html, url):
        response = Mock()
        response.status_code = 200
        response.text = html
        response.url = url
        response.raise_for_status = Mock()
        return response

    def test_crawl_by_model_upserts_vehicle_knowledge(self):
        html = """
        <html>
          <body>
            <div class="lemmaSummary_O3o_W J-summary">比亚迪海豹是纯电动轿车。</div>
            <div class="basic-info J-basic-info">
              <dl>
                <dt class="basicInfo-item name">所属品牌</dt>
                <dd class="basicInfo-item value">比亚迪</dd>
                <dt class="basicInfo-item name">电池类型</dt>
                <dd class="basicInfo-item value">磷酸铁锂电池</dd>
              </dl>
            </div>
          </body>
        </html>
        """
        with patch("requests.get", return_value=self._mock_response(html, "https://baike.baidu.com/item/比亚迪海豹")):
            response = self.client.post(
                self.api("vehicleknowledge/crawlByModel"),
                data=json.dumps({"vehiclemodel": "比亚迪海豹"}),
                content_type="application/json",
                **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)

        VehicleKnowledge = self.get_model_or_fail("vehicleknowledge")
        record = VehicleKnowledge.objects.get(vehiclemodel="比亚迪海豹")
        self.assertEqual(record.manufacturer, "比亚迪")
        self.assertEqual(record.batterytype, "磷酸铁锂电池")
        self.assertEqual(record.crawlstatus, "成功")

        updated_html = """
        <html>
          <body>
            <div class="lemmaSummary_O3o_W J-summary">比亚迪海豹冠军版。</div>
            <div class="basic-info J-basic-info">
              <dl>
                <dt class="basicInfo-item name">所属品牌</dt>
                <dd class="basicInfo-item value">比亚迪汽车</dd>
              </dl>
            </div>
          </body>
        </html>
        """
        with patch("requests.get", return_value=self._mock_response(updated_html, "https://baike.baidu.com/item/比亚迪海豹")):
            response = self.client.post(
                self.api("vehicleknowledge/crawlByModel"),
                data=json.dumps({"vehiclemodel": "比亚迪海豹"}),
                content_type="application/json",
                **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(VehicleKnowledge.objects.filter(vehiclemodel="比亚迪海豹").count(), 1)
        record.refresh_from_db()
        self.assertEqual(record.manufacturer, "比亚迪汽车")

    def test_crawl_batch_deduplicates_models_from_drivinglog(self):
        self.log_a.vehiclemodel = "比亚迪海豹"
        self.log_a.save(update_fields=["vehiclemodel"])
        self.log_b.vehiclemodel = "比亚迪海豹"
        self.log_b.save(update_fields=["vehiclemodel"])
        self.log_c.vehiclemodel = "特斯拉Model Y"
        self.log_c.save(update_fields=["vehiclemodel"])

        def side_effect(url, *args, **kwargs):
            if "比亚迪海豹" in url:
                return self._mock_response(
                    """
                    <html><body>
                    <div class="lemmaSummary_O3o_W J-summary">海豹简介</div>
                    <div class="basic-info J-basic-info">
                      <dl><dt class="basicInfo-item name">所属品牌</dt><dd class="basicInfo-item value">比亚迪</dd></dl>
                    </div>
                    </body></html>
                    """,
                    url,
                )
            return self._mock_response(
                """
                <html><body>
                <div class="lemmaSummary_O3o_W J-summary">Model Y简介</div>
                <div class="basic-info J-basic-info">
                  <dl><dt class="basicInfo-item name">所属品牌</dt><dd class="basicInfo-item value">特斯拉</dd></dl>
                </div>
                </body></html>
                """,
                url,
            )

        with patch("requests.get", side_effect=side_effect):
            response = self.client.post(
                self.api("vehicleknowledge/crawlBatch"),
                data=json.dumps({}),
                content_type="application/json",
                **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)

        VehicleKnowledge = self.get_model_or_fail("vehicleknowledge")
        self.assertEqual(VehicleKnowledge.objects.count(), 2)
        self.assertTrue(VehicleKnowledge.objects.filter(vehiclemodel="比亚迪海豹").exists())
        self.assertTrue(VehicleKnowledge.objects.filter(vehiclemodel="特斯拉Model Y").exists())

    def test_crawl_by_model_falls_back_to_search_when_baike_forbidden(self):
        def side_effect(url, *args, **kwargs):
            if "baike.baidu.com" in url:
                response = Mock()
                response.status_code = 403
                response.text = "<html><title>百度安全验证</title></html>"
                response.url = url
                response.raise_for_status = Mock(side_effect=Exception("403 Client Error: Forbidden for url: %s" % url))
                return response
            return self._mock_response(
                """
                <html>
                  <body>
                    <li class="res-list">
                      <h3><a href="https://baike.so.com/doc/30506231-32301401.html">比亚迪海豹_360百科</a></h3>
                      <p>比亚迪海豹是比亚迪旗下纯电动汽车，CLTC工况纯电续航里程提供550公里、650公里、700公里。</p>
                    </li>
                  </body>
                </html>
                """,
                url,
            )

        with patch("requests.get", side_effect=side_effect):
            response = self.client.post(
                self.api("vehicleknowledge/crawlByModel"),
                data=json.dumps({"vehiclemodel": "比亚迪海豹"}),
                content_type="application/json",
                **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)

        VehicleKnowledge = self.get_model_or_fail("vehicleknowledge")
        record = VehicleKnowledge.objects.get(vehiclemodel="比亚迪海豹")
        self.assertEqual(record.crawlstatus, "成功")
        self.assertIn("纯电续航", record.summary)
        self.assertIn("baike.so.com", record.sourceurl)

    def test_crawl_by_model_rejects_irrelevant_search_result(self):
        def side_effect(url, *args, **kwargs):
            if "baike.baidu.com" in url:
                response = Mock()
                response.status_code = 403
                response.text = "<html><title>百度安全验证</title></html>"
                response.url = url
                response.raise_for_status = Mock(side_effect=Exception("403 Client Error: Forbidden for url: %s" % url))
                return response
            return self._mock_response(
                """
                <html>
                  <body>
                    <li class="res-list">
                      <h3><a href="https://shopmodela.com/">Modela</a></h3>
                      <p>handmade in Oaxaca, Mexico. Handwoven mexican rugs and pottery.</p>
                    </li>
                  </body>
                </html>
                """,
                url,
            )

        with patch("requests.get", side_effect=side_effect):
            response = self.client.post(
                self.api("vehicleknowledge/crawlByModel"),
                data=json.dumps({"vehiclemodel": "Model-A"}),
                content_type="application/json",
                **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotEqual(payload["code"], 0)

        VehicleKnowledge = self.get_model_or_fail("vehicleknowledge")
        record = VehicleKnowledge.objects.get(vehiclemodel="Model-A")
        self.assertEqual(record.crawlstatus, "失败")

    def test_crawl_by_model_uses_builtin_demo_fallback_when_public_sources_blocked(self):
        def side_effect(url, *args, **kwargs):
            response = Mock()
            response.status_code = 403 if "baike.baidu.com" in url else 200
            response.url = url
            if "baike.baidu.com" in url:
                response.text = "<html><title>百度安全验证</title></html>"
                response.raise_for_status = Mock(
                    side_effect=Exception("403 Client Error: Forbidden for url: %s" % url)
                )
            else:
                response.text = "<html><title>访问异常页面</title></html>"
                response.raise_for_status = Mock()
            return response

        with patch("requests.get", side_effect=side_effect):
            response = self.client.post(
                self.api("vehicleknowledge/crawlByModel"),
                data=json.dumps({"vehiclemodel": "比亚迪海豹"}),
                content_type="application/json",
                **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)

        VehicleKnowledge = self.get_model_or_fail("vehicleknowledge")
        record = VehicleKnowledge.objects.get(vehiclemodel="比亚迪海豹")
        self.assertEqual(record.crawlstatus, "成功")
        self.assertTrue(record.summary)
        self.assertIn("答辩演示", record.sourceurl)

    def test_crawl_by_model_prefers_builtin_demo_data_when_search_result_too_sparse(self):
        def side_effect(url, *args, **kwargs):
            if "baike.baidu.com" in url:
                response = Mock()
                response.status_code = 403
                response.text = "<html><title>百度安全验证</title></html>"
                response.url = url
                response.raise_for_status = Mock(
                    side_effect=Exception("403 Client Error: Forbidden for url: %s" % url)
                )
                return response

            return self._mock_response(
                """
                <html>
                  <body>
                    <li class="b_algo">
                      <h2><a href="https://www.autohome.com.cn/5213/">小鹏P7</a></h2>
                      <div class="b_caption"><p>小鹏P7是一款热门纯电轿车。</p></div>
                    </li>
                  </body>
                </html>
                """,
                url,
            )

        with patch("requests.get", side_effect=side_effect):
            response = self.client.post(
                self.api("vehicleknowledge/crawlByModel"),
                data=json.dumps({"vehiclemodel": "小鹏P7"}),
                content_type="application/json",
                **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)

        VehicleKnowledge = self.get_model_or_fail("vehicleknowledge")
        record = VehicleKnowledge.objects.get(vehiclemodel="小鹏P7")
        self.assertEqual(record.crawlstatus, "成功")
        self.assertEqual(record.manufacturer, "小鹏汽车")
        self.assertIn("702km", record.officialrange)
        self.assertIn("答辩演示", record.sourceurl)


class FeatureSchemaSyncCommandTest(TransactionTestCase):
    def _table_exists(self, table_name):
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE %s", [table_name])
            return cursor.fetchone() is not None

    def _column_exists(self, table_name, column_name):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = %s
                  AND column_name = %s
                """,
                [table_name, column_name],
            )
            return cursor.fetchone() is not None

    def test_sync_feature_schema_recreates_missing_vehicleknowledge_table(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS `vehicleknowledge`")

        self.assertFalse(self._table_exists("vehicleknowledge"))

        call_command("sync_feature_schema", verbosity=0)

        self.assertTrue(self._table_exists("vehicleknowledge"))

    def test_sync_feature_schema_adds_prediction_upgrade_columns(self):
        call_command("sync_feature_schema", verbosity=0)

        self.assertTrue(self._column_exists("drivinglogforecast", "predictedpowerconsumption"))
        self.assertTrue(self._column_exists("drivinglogforecast", "risklevel"))
        self.assertTrue(self._column_exists("drivinglogforecast", "modelname"))
        self.assertTrue(self._column_exists("drivinglogforecast", "modelversion"))
        self.assertTrue(self._column_exists("drivinglogforecast", "majorfactors"))


class DemoDataPrepareCommandTest(BaseApiTestCase):
    def test_prepare_demo_data_normalizes_models_and_clears_vehicleknowledge(self):
        self.log_a.vehiclemodel = "Model-A"
        self.log_a.vehiclenumber = "CAR-001"
        self.log_a.save(update_fields=["vehiclemodel", "vehiclenumber"])

        self.log_b.vehiclemodel = "M1"
        self.log_b.vehiclenumber = "C1"
        self.log_b.save(update_fields=["vehiclemodel", "vehiclenumber"])

        VehicleKnowledge = self.get_model_or_fail("vehicleknowledge")
        VehicleKnowledge.objects.create(vehiclemodel="Model-A", crawlstatus="成功", summary="old")

        call_command("prepare_demo_data", verbosity=0)

        self.log_a.refresh_from_db()
        self.log_b.refresh_from_db()

        self.assertEqual(self.log_a.vehiclemodel, "比亚迪海豹")
        self.assertEqual(self.log_b.vehiclemodel, "五菱宏光MINIEV")
        self.assertEqual(self.log_b.vehiclenumber, "MINI-001")
        self.assertEqual(VehicleKnowledge.objects.count(), 0)


class DrivinglogCleansePreviewTest(BaseApiTestCase):
    def test_cleanse_preview_flags_negative_battery_and_time_errors(self):
        Drivinglog = self.get_model_or_fail("drivinglog")
        Drivinglog.objects.create(
            vehiclenumber="BAD-001",
            vehiclemodel="演示车型",
            batterycapacity=60,
            batterylevel=-5,
            accumulatedmileage=100,
            starttime="2026-01-02 10:00:00",
            endtime="2026-01-02 09:00:00",
            powerconsumption=-3,
            drivingbehaviorrating=80,
        )

        response = self.client.post(
            self.api("drivinglog/cleanse-preview"),
            data=json.dumps({}),
            content_type="application/json",
            **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertGreaterEqual(payload["data"]["invalid_count"], 1)
        self.assertGreaterEqual(payload["data"]["issues"]["invalid_batterylevel"], 1)
        self.assertGreaterEqual(payload["data"]["issues"]["time_order_error"], 1)
        self.assertGreaterEqual(payload["data"]["issues"]["negative_powerconsumption"], 1)


class ForecastTrainingCommandTest(BaseApiTestCase):
    def test_train_ml_models_writes_model_and_metrics_artifacts(self):
        call_command("train_ml_models", verbosity=0)
        self.assertTrue(os.path.exists("artifacts/models/drivinglog_power_model.pkl"))
        self.assertTrue(os.path.exists("artifacts/models/drivinglog_life_model.pkl"))
        self.assertTrue(os.path.exists("artifacts/reports/ml_metrics.json"))

    def test_train_ml_models_writes_neural_baseline_artifacts(self):
        call_command("train_ml_models", verbosity=0)
        self.assertTrue(os.path.exists("artifacts/models/drivinglog_power_mlp_model.pkl"))
        self.assertTrue(os.path.exists("artifacts/models/drivinglog_life_mlp_model.pkl"))
        self.assertTrue(os.path.exists("artifacts/reports/ml_comparison_metrics.json"))

    @patch("main.management.commands.train_ml_models.save_ml_artifacts")
    @patch("main.management.commands.train_ml_models.train_neural_baseline_bundle")
    @patch("main.management.commands.train_ml_models.train_ml_bundle")
    def test_train_ml_models_supports_explicit_raw_excel_source(
        self,
        mock_train_ml_bundle,
        mock_train_neural_baseline_bundle,
        mock_save_ml_artifacts,
    ):
        mock_train_ml_bundle.return_value = (
            {"power": object(), "life": object()},
            {"power": {"MAE": 1.0}, "life": {"MAE": 2.0}},
            {"source_type": "raw_excel", "sample_count": 21507},
        )
        mock_train_neural_baseline_bundle.return_value = (
            {"power_mlp": object(), "life_mlp": object()},
            {"power_mlp": {"MAE": 1.1}, "life_mlp": {"MAE": 2.1}},
            {"source_type": "raw_excel", "sample_count": 21507},
        )
        mock_save_ml_artifacts.return_value = {
            "metrics": "artifacts/reports/ml_metrics.json",
            "comparison_metrics": "artifacts/reports/ml_comparison_metrics.json",
        }

        call_command(
            "train_ml_models",
            "--source",
            "excel",
            "--excel-path",
            "docs/待提交/新数据21507条【备份】.xlsx",
            verbosity=0,
        )

        ml_kwargs = mock_train_ml_bundle.call_args.kwargs
        mlp_kwargs = mock_train_neural_baseline_bundle.call_args.kwargs
        self.assertIsNone(ml_kwargs["queryset_or_records"])
        self.assertEqual(ml_kwargs["excel_path"], "docs/待提交/新数据21507条【备份】.xlsx")
        self.assertIsNone(mlp_kwargs["queryset_or_records"])
        self.assertEqual(mlp_kwargs["excel_path"], "docs/待提交/新数据21507条【备份】.xlsx")


class ForecastMetricsCommandTest(BaseApiTestCase):
    def test_evaluate_ml_models_prints_mae_rmse_r2(self):
        output = io.StringIO()
        call_command("evaluate_ml_models", stdout=output)
        content = output.getvalue()
        self.assertIn("MAE", content)
        self.assertIn("RMSE", content)
        self.assertIn("R2", content)


class ForecastDLCommandTest(BaseApiTestCase):
    def setUp(self):
        super().setUp()
        if os.path.exists("artifacts"):
            import shutil

            shutil.rmtree("artifacts")

    def test_prepare_sequence_data_writes_dataset_artifacts(self):
        call_command("prepare_sequence_data", verbosity=0)
        self.assertTrue(os.path.exists("artifacts/sequence/drivinglog_sequence_dataset.npz"))
        self.assertTrue(os.path.exists("artifacts/sequence/drivinglog_sequence_meta.json"))

    @patch("main.management.commands.prepare_sequence_data.prepare_sequence_dataset")
    def test_prepare_sequence_data_supports_explicit_excel_source(self, mock_prepare_sequence_dataset):
        mock_prepare_sequence_dataset.return_value = {
            "metadata": {
                "source_type": "raw_excel",
                "sample_count": 12,
            }
        }

        call_command(
            "prepare_sequence_data",
            "--source",
            "excel",
            "--excel-path",
            "docs/待提交/新数据21507条【备份】.xlsx",
            verbosity=0,
        )

        kwargs = mock_prepare_sequence_dataset.call_args.kwargs
        self.assertIsNone(kwargs["queryset_or_records"])
        self.assertEqual(kwargs["excel_path"], "docs/待提交/新数据21507条【备份】.xlsx")

    def test_train_dl_model_writes_model_and_metrics_artifacts(self):
        call_command("train_dl_model", verbosity=0)
        self.assertTrue(os.path.exists("artifacts/reports/dl_metrics.json"))
        self.assertTrue(os.path.exists("artifacts/reports/dl_bundle_manifest.json"))

    @patch("main.management.commands.train_dl_model.train_dl_bundle")
    def test_train_dl_model_supports_explicit_table_source(self, mock_train_dl_bundle):
        mock_train_dl_bundle.return_value = {
            "manifest": {
                "backend": "sklearn_mlp_fallback",
                "version": "dl-20260412150000",
            },
            "metrics": {
                "power_dl": {"MAE": 0.5},
                "life_dl": {"MAE": 1.0},
            },
        }

        call_command("train_dl_model", "--source", "table", verbosity=0)

        kwargs = mock_train_dl_bundle.call_args.kwargs
        self.assertEqual(kwargs["queryset_or_records"].model, drivinglog)
        self.assertIsNone(kwargs["excel_path"])

    def test_compare_models_writes_compare_report(self):
        call_command("compare_models", verbosity=0)
        compare_path = "artifacts/reports/model_compare.json"
        self.assertTrue(os.path.exists(compare_path))
        with open(compare_path, "r", encoding="utf-8") as compare_file:
            payload = json.load(compare_file)
        self.assertIn("ml", payload)
        self.assertIn("dl", payload)


class DrivinglogDisplayRebuildCommandTest(BaseApiTestCase):
    @patch("main.management.commands.rebuild_drivinglog_from_summary_excel.load_summary_display_records")
    def test_rebuild_command_replaces_drivinglog_with_summary_excel_rows(self, mock_load_summary_display_records):
        mock_load_summary_display_records.return_value = [
            {
                "vehiclenumber": "SUM-001",
                "vehiclemodel": "GAC Aion S",
                "batterycapacity": 70,
                "batterylife": 72,
                "accumulatedmileage": 120,
                "starttime": "2026-04-10 08:00:00",
                "endtime": "2026-04-10 09:00:00",
                "averagespeed": 55,
                "batterylevel": 62,
                "powerconsumption": 14,
                "drivingroute": "城市通勤",
                "collectiontime": "2026-04-10 09:05:00",
                "rapidaccelerationtimes": 1,
                "numberofrapiddecelerations": 1,
                "numberofspeedingincidents": 0,
                "energysavingsuggestions": "保持平稳驾驶",
                "drivingbehaviorrating": 86,
            },
            {
                "vehiclenumber": "SUM-002",
                "vehiclemodel": "Tesla Model 3",
                "batterycapacity": 78,
                "batterylife": 65,
                "accumulatedmileage": 160,
                "starttime": "2026-04-11 10:00:00",
                "endtime": "2026-04-11 11:20:00",
                "averagespeed": 68,
                "batterylevel": 57,
                "powerconsumption": 16,
                "drivingroute": "高架快速路",
                "collectiontime": "2026-04-11 11:25:00",
                "rapidaccelerationtimes": 2,
                "numberofrapiddecelerations": 2,
                "numberofspeedingincidents": 1,
                "energysavingsuggestions": "减少急加速",
                "drivingbehaviorrating": 79,
            },
        ]

        call_command("rebuild_drivinglog_from_summary_excel", verbosity=0)

        self.assertEqual(drivinglog.objects.count(), 2)
        first = drivinglog.objects.get(vehiclenumber="SUM-001")
        self.assertEqual(first.vehiclemodel, "GAC Aion S")
        self.assertEqual(first.storeupnum, 0)
        self.assertEqual(first.discussnum, 0)


class ForecastApiTest(BaseApiTestCase):
    def setUp(self):
        super().setUp()
        if os.path.exists("artifacts"):
            import shutil

            shutil.rmtree("artifacts")

    def test_predict_endpoint_returns_prediction_and_persists_record(self):
        response = self.client.post(
            self.api("drivinglogforecast/predict"),
            data=json.dumps(
                {
                    "vehiclemodel": "Model-A",
                    "batterycapacity": 90,
                    "accumulatedmileage": 160,
                    "drivingbehaviorrating": 82,
                    "drivingroute": "城市通勤",
                    "averagespeed": 58,
                    "batterylevel": 70,
                    "rapidaccelerationtimes": 1,
                    "numberofrapiddecelerations": 1,
                    "numberofspeedingincidents": 0,
                }
            ),
            content_type="application/json",
            **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertIn("predictedpowerconsumption", payload["data"])
        self.assertIn("batterylife", payload["data"])
        self.assertIn("risklevel", payload["data"])
        self.assertIn("majorfactors", payload["data"])

        Forecast = self.get_model_or_fail("drivinglogforecast")
        record = Forecast.objects.latest("id")
        self.assertIsNotNone(record.predictedpowerconsumption)
        self.assertTrue(record.risklevel)
        self.assertTrue(record.modelname)

    def test_metrics_endpoint_returns_trained_targets(self):
        response = self.client.get(
            self.api("drivinglogforecast/metrics"),
            **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertIn("power", payload["data"]["metrics"])
        self.assertIn("life", payload["data"]["metrics"])
        self.assertIn("power_mlp", payload["data"]["comparison_metrics"])
        self.assertIn("life_mlp", payload["data"]["comparison_metrics"])

    def test_scenarios_endpoint_returns_multiple_scenarios(self):
        response = self.client.post(
            self.api("drivinglogforecast/scenarios"),
            data=json.dumps(
                {
                    "vehiclemodel": "Model-B",
                    "batterycapacity": 100,
                    "accumulatedmileage": 220,
                    "drivingbehaviorrating": 76,
                    "drivingroute": "市区-高架混合",
                    "averagespeed": 64,
                    "batterylevel": 55,
                }
            ),
            content_type="application/json",
            **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertGreaterEqual(len(payload["data"]["scenarios"]), 3)
        first_scenario = payload["data"]["scenarios"][0]
        self.assertIn("name", first_scenario)
        self.assertIn("prediction", first_scenario)
        self.assertIn("risklevel", first_scenario["prediction"])

    def test_compare_endpoint_returns_ml_and_dl_sections(self):
        response = self.client.post(
            self.api("drivinglogforecast/compare"),
            data=json.dumps(
                {
                    "vehiclemodel": "Model-B",
                    "batterycapacity": 100,
                    "accumulatedmileage": 220,
                    "drivingbehaviorrating": 76,
                    "drivingroute": "市区-高架混合",
                    "averagespeed": 64,
                    "batterylevel": 55,
                }
            ),
            content_type="application/json",
            **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertIn("ml", payload["data"])
        self.assertIn("dl", payload["data"])
        self.assertIn("comparison", payload["data"])
        self.assertIn("risklevel", payload["data"]["dl"])
        self.assertIn("backend", payload["data"]["dl"])

    @patch("main.Drivinglogforecast_v.get_battery_life_artifact_paths")
    def test_nasa_experiment_endpoint_returns_summary_metrics_and_figures(self, mock_artifact_paths):
        import tempfile

        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        artifact_dir = os.path.join(temp_dir.name, "artifacts", "battery_life")
        figure_dir = os.path.join(artifact_dir, "figures")
        os.makedirs(figure_dir, exist_ok=True)

        dataset_manifest_path = os.path.join(artifact_dir, "nasa_life_dataset_manifest.json")
        training_manifest_path = os.path.join(artifact_dir, "nasa_life_training_manifest.json")
        metrics_path = os.path.join(artifact_dir, "nasa_life_metrics.json")
        capacity_curve_path = os.path.join(figure_dir, "nasa_capacity_degradation.png")
        soh_plot_path = os.path.join(figure_dir, "nasa_soh_prediction.png")
        rul_plot_path = os.path.join(figure_dir, "nasa_rul_prediction.png")

        with open(dataset_manifest_path, "w", encoding="utf-8") as manifest_file:
            json.dump(
                {
                    "dataset": "NASA PCoE Battery Aging",
                    "source_url": "https://example.com/nasa.zip",
                    "battery_count": 34,
                    "sample_count": 5308,
                    "generated_at": "2026-04-12 14:48:36",
                },
                manifest_file,
                ensure_ascii=False,
            )
        with open(training_manifest_path, "w", encoding="utf-8") as manifest_file:
            json.dump(
                {
                    "dataset": "NASA PCoE Battery Aging",
                    "model_family": "RandomForest(SOH)+GradientBoosting(RUL)",
                    "split_strategy": "group_holdout_by_battery",
                    "feature_columns": {
                        "soh": ["cycle_index", "voltage_mean"],
                        "rul": ["cycle_index", "capacity"],
                    },
                    "train_batteries": ["B0005", "B0006"],
                    "test_batteries": ["B0007"],
                    "sample_count": 5308,
                    "battery_count": 34,
                    "updated_at": "2026-04-12 15:03:25",
                },
                manifest_file,
                ensure_ascii=False,
            )
        with open(metrics_path, "w", encoding="utf-8") as metrics_file:
            json.dump(
                {
                    "soh": {"MAE": 0.0589, "RMSE": 0.115, "R2": 0.6001, "sample_count": 5308},
                    "rul": {"MAE": 13.33, "RMSE": 24.99, "R2": 0.4497, "sample_count": 5308},
                },
                metrics_file,
                ensure_ascii=False,
            )
        for file_path in (capacity_curve_path, soh_plot_path, rul_plot_path):
            with open(file_path, "wb") as image_file:
                image_file.write(
                    base64.b64decode(
                        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO0pP3sAAAAASUVORK5CYII="
                    )
                )

        mock_artifact_paths.return_value = {
            "artifact_dir": artifact_dir,
            "figure_dir": figure_dir,
            "manifest": dataset_manifest_path,
            "training_manifest": training_manifest_path,
            "metrics": metrics_path,
            "capacity_curve": capacity_curve_path,
            "soh_prediction_plot": soh_plot_path,
            "rul_prediction_plot": rul_plot_path,
        }

        response = self.client.get(
            self.api("drivinglogforecast/nasaExperiment"),
            **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertTrue(payload["data"]["available"])
        self.assertEqual(payload["data"]["dataset"]["dataset"], "NASA PCoE Battery Aging")
        self.assertEqual(payload["data"]["experiment"]["split_strategy"], "group_holdout_by_battery")
        self.assertIn("soh", payload["data"]["metrics"])
        self.assertEqual(len(payload["data"]["figures"]), 3)
        self.assertTrue(payload["data"]["figures"][0]["url"].endswith("/nasaFigure/nasa_capacity_degradation.png"))

        figure_response = self.client.get(
            self.api("drivinglogforecast/nasaFigure/nasa_capacity_degradation.png"),
            **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
        )
        self.assertEqual(figure_response.status_code, 200)
        self.assertEqual(figure_response["Content-Type"], "image/png")


class StoreupFlowTest(BaseApiTestCase):
    def test_toggle_storeup_and_sync_counter(self):
        response = self.client.post(
            self.api("storeup/toggle"),
            data=json.dumps({"refid": self.log_a.id, "tablename": "drivinglog"}),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)

        Storeup = self.get_model_or_fail("storeup")
        self.assertTrue(
            Storeup.objects.filter(userid=self.front_user.id, refid=self.log_a.id, tablename="drivinglog").exists()
        )
        self.log_a.refresh_from_db()
        self.assertEqual(getattr(self.log_a, "storeupnum", None), 1)

        response = self.client.post(
            self.api("storeup/toggle"),
            data=json.dumps({"refid": self.log_a.id, "tablename": "drivinglog"}),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)

        self.assertFalse(
            Storeup.objects.filter(userid=self.front_user.id, refid=self.log_a.id, tablename="drivinglog").exists()
        )
        self.log_a.refresh_from_db()
        self.assertEqual(getattr(self.log_a, "storeupnum", None), 0)

    def test_storeup_page_fills_fallback_picture_for_legacy_records(self):
        Storeup = self.get_model_or_fail("storeup")
        Storeup.objects.create(
            userid=self.front_user.id,
            refid=self.log_a.id,
            tablename="drivinglog",
            name=self.log_a.vehiclenumber,
            picture="",
            type="1",
            inteltype="vehiclemodel",
        )

        response = self.client.get(
            self.api("storeup/page"),
            {"page": 1, "limit": 10},
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertEqual(payload["data"]["list"][0]["picture"], "upload/image1.jpg")


class DiscussFlowTest(BaseApiTestCase):
    def test_add_comment_and_reply_sync_counter(self):
        response = self.client.post(
            self.api("discussdrivinglog/add"),
            data=json.dumps({"refid": self.log_a.id, "content": "这条日志很有参考价值"}),
            content_type="application/json",
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)

        DiscussDrivinglog = self.get_model_or_fail("discussdrivinglog")
        comment = DiscussDrivinglog.objects.get(id=payload["data"])
        self.assertEqual(comment.userid, self.front_user.id)
        self.assertEqual(comment.content, "这条日志很有参考价值")

        self.log_a.refresh_from_db()
        self.assertEqual(getattr(self.log_a, "discussnum", None), 1)

        reply_payload = json.dumps(
            [
                {
                    "id": 1,
                    "userid": self.admin_user.id,
                    "nickname": "管理员",
                    "avatarurl": "",
                    "content": "收到，感谢反馈",
                    "addtime": "2026-04-11 10:00:00",
                }
            ],
            ensure_ascii=False,
        )
        response = self.client.post(
            self.api("discussdrivinglog/update"),
            data=json.dumps({"id": comment.id, "reply": reply_payload}),
            content_type="application/json",
            **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)

        comment.refresh_from_db()
        self.assertEqual(comment.reply, reply_payload)


class RecommendationTest(BaseApiTestCase):
    def test_auto_sort2_prefers_matching_vehiclemodel_or_route(self):
        Storeup = self.get_model_or_fail("storeup")
        Storeup.objects.create(
            userid=self.front_user.id,
            refid=self.log_a.id,
            tablename="drivinglog",
            name=self.log_a.vehiclenumber,
            picture="",
            type="1",
            inteltype="vehiclemodel",
        )

        response = self.client.get(
            self.api("drivinglog/autoSort2"),
            {"page": 1, "limit": 10},
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertIn("list", payload["data"])
        ids = [item["id"] for item in payload["data"]["list"]]
        self.assertIn(self.log_b.id, ids)
        self.assertNotEqual(ids[0], self.log_c.id)

    def test_auto_sort2_falls_back_when_user_has_no_preference(self):
        response = self.client.get(
            self.api("drivinglog/autoSort2"),
            {"page": 1, "limit": 10},
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertIn("list", payload["data"])
        self.assertGreaterEqual(len(payload["data"]["list"]), 1)


class UserUtilityTest(BaseApiTestCase):
    def test_users_account_list_returns_account_data(self):
        response = self.client.get(
            self.api("users/accountList"),
            **self.auth_headers(table_name="users", params={"id": self.admin_user.id}),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertIsInstance(payload["data"], list)
        self.assertTrue(any(item["account"] == self.admin_user.username for item in payload["data"]))

    def test_user_auto_sort2_returns_standard_page_payload(self):
        response = self.client.get(
            self.api("user/autoSort2"),
            {"page": 1, "limit": 10},
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        self.assertIn("list", payload["data"])


class NasaBatteryLifeExperimentTest(TestCase):
    def test_build_life_frame_computes_soh_and_rul_from_discharge_capacities(self):
        from main.battery_life.nasa_dataset import build_life_frame

        frame = build_life_frame(
            [
                {
                    "battery_id": "B0005",
                    "cycle_index": 1,
                    "capacity": 2.0,
                    "voltage_mean": 3.7,
                    "current_mean": -1.5,
                    "temperature_mean": 28.0,
                    "duration_seconds": 3200,
                },
                {
                    "battery_id": "B0005",
                    "cycle_index": 2,
                    "capacity": 1.6,
                    "voltage_mean": 3.6,
                    "current_mean": -1.5,
                    "temperature_mean": 29.0,
                    "duration_seconds": 3300,
                },
                {
                    "battery_id": "B0005",
                    "cycle_index": 3,
                    "capacity": 1.39,
                    "voltage_mean": 3.5,
                    "current_mean": -1.5,
                    "temperature_mean": 30.0,
                    "duration_seconds": 3400,
                },
            ],
            eol_capacity=1.4,
        )

        self.assertEqual(len(frame), 3)
        self.assertAlmostEqual(frame.iloc[0]["soh"], 1.0)
        self.assertAlmostEqual(frame.iloc[1]["soh"], 0.8)
        self.assertEqual(frame.iloc[0]["rul"], 2)
        self.assertEqual(frame.iloc[1]["rul"], 1)
        self.assertEqual(frame.iloc[2]["rul"], 0)

    def test_train_real_life_models_writes_soh_and_rul_artifacts(self):
        import shutil
        import tempfile

        from main.battery_life.trainers import train_real_life_models

        rows = []
        for battery_id, start_capacity in (("B0005", 2.0), ("B0006", 1.95)):
            for cycle_index in range(1, 13):
                capacity = start_capacity - cycle_index * 0.04
                rows.append(
                    {
                        "battery_id": battery_id,
                        "cycle_index": cycle_index,
                        "capacity": capacity,
                        "soh": capacity / start_capacity,
                        "rul": 12 - cycle_index,
                        "voltage_mean": 3.8 - cycle_index * 0.01,
                        "current_mean": -1.4,
                        "temperature_mean": 27 + cycle_index * 0.2,
                        "duration_seconds": 3000 + cycle_index * 10,
                    }
                )

        temp_dir = tempfile.mkdtemp()
        try:
            result = train_real_life_models(rows, base_dir=temp_dir)
            self.assertTrue(os.path.exists(result["paths"]["soh_model"]))
            self.assertTrue(os.path.exists(result["paths"]["rul_model"]))
            self.assertTrue(os.path.exists(result["paths"]["metrics"]))
            self.assertTrue(os.path.exists(result["paths"]["capacity_curve"]))
            self.assertTrue(os.path.exists(result["paths"]["soh_prediction_plot"]))
            self.assertTrue(os.path.exists(result["paths"]["rul_prediction_plot"]))
            self.assertEqual(result["manifest"]["dataset"], "NASA PCoE Battery Aging")
            self.assertIn("soh", result["metrics"])
            self.assertIn("rul", result["metrics"])
            self.assertEqual(result["manifest"]["split_strategy"], "group_holdout_by_battery")
            self.assertNotIn("capacity", result["manifest"]["feature_columns"]["soh"])
            self.assertIn("capacity", result["manifest"]["feature_columns"]["rul"])
            self.assertEqual(result["metrics"]["soh"]["evaluation_mode"], "group_holdout")
            self.assertEqual(result["metrics"]["rul"]["evaluation_mode"], "group_holdout")
            self.assertTrue(
                set(result["manifest"]["train_batteries"]).isdisjoint(set(result["manifest"]["test_batteries"]))
            )
        finally:
            shutil.rmtree(temp_dir)

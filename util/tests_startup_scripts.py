import os
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class StartupScriptsTest(unittest.TestCase):
    def _read(self, relative_path):
        path = os.path.join(PROJECT_ROOT, relative_path)
        with open(path, encoding="utf-8") as file_obj:
            return file_obj.read()

    def test_backend_start_scripts_exist(self):
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "bin", "start_backend.ps1")))
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "bin", "start_project.ps1")))
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "bin", "run_backend_wsgi.py")))
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "bin", "bootstrap_local.ps1")))
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "bin", "bootstrap_local_db.py")))
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "bin", "export_migration_bundle.ps1")))
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "bin", "restore_migration_bundle.ps1")))
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "bin", "export_mysql_dump.py")))
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "bin", "import_mysql_dump.py")))

    def test_wsgi_runner_bootstraps_project_root_into_sys_path(self):
        content = self._read("bin/run_backend_wsgi.py")
        self.assertRegex(content, r"import\s+sys")
        self.assertRegex(content, r"sys\.path\.insert\(0,\s*PROJECT_ROOT\)")
        self.assertRegex(content, r"PROJECT_ROOT\s*=")

    def test_backend_start_script_uses_env_file_and_wsgi_runner(self):
        content = self._read("bin/start_backend.ps1")
        self.assertIn(".env", content)
        self.assertRegex(content, r"run_backend_wsgi\.py")
        self.assertRegex(content, r"APP_BACKEND_PORT")
        self.assertNotRegex(content, r"\[string\]\$Host\b")
        self.assertRegex(content, r"\[string\]\$BackendHost\b")

    def test_project_start_script_bootstraps_backend_and_frontend(self):
        content = self._read("bin/start_project.ps1")
        self.assertRegex(content, r"start_backend\.ps1")
        self.assertRegex(content, r"npm\s+run\s+serve")
        self.assertRegex(content, r"APP_FRONTEND_PORT")
        self.assertRegex(content, r"['\"]-BackendHost['\"]")
        self.assertNotRegex(content, r"['\"]-Host['\"]")

    def test_bootstrap_script_bootstraps_windows_local_environment(self):
        content = self._read("bin/bootstrap_local.ps1")
        self.assertRegex(content, r"\.venv")
        self.assertRegex(content, r"pip\s+install\s+-r\s+requirements\.txt")
        self.assertRegex(content, r"npm\s+install")
        self.assertRegex(content, r"\.env\.example")
        self.assertRegex(content, r"migrate\s+--fake-initial")
        self.assertRegex(content, r"sync_feature_schema")
        self.assertRegex(content, r"start_project\.ps1")

    def test_bootstrap_database_script_mentions_sql_dump_and_runtime_database_name(self):
        content = self._read("bin/bootstrap_local_db.py")
        self.assertRegex(content, r"diandong5k56la1f\.sql")
        self.assertRegex(content, r"DB_NAME")
        self.assertRegex(content, r"CREATE DATABASE")

    def test_readme_promotes_windows_local_bootstrap(self):
        content = self._read("README.md")
        self.assertRegex(content, r"bootstrap_local\.ps1")
        self.assertRegex(content, r"Windows")

    def test_export_migration_script_packages_database_and_runtime_assets(self):
        content = self._read("bin/export_migration_bundle.ps1")
        self.assertRegex(content, r"export_mysql_dump\.py")
        self.assertRegex(content, r"media")
        self.assertRegex(content, r"artifacts")
        self.assertRegex(content, r"datasets")
        self.assertRegex(content, r"Compress-Archive")
        self.assertRegex(content, r"\.env")
        self.assertRegex(content, r"config\.ini")

    def test_restore_migration_script_restores_database_and_bootstraps_dependencies(self):
        content = self._read("bin/restore_migration_bundle.ps1")
        self.assertRegex(content, r"Expand-Archive")
        self.assertRegex(content, r"import_mysql_dump\.py")
        self.assertRegex(content, r"bootstrap_local\.ps1")
        self.assertRegex(content, r"media")
        self.assertRegex(content, r"artifacts")
        self.assertRegex(content, r"datasets")

    def test_readme_documents_migration_bundle_scripts(self):
        content = self._read("README.md")
        self.assertRegex(content, r"export_migration_bundle\.ps1")
        self.assertRegex(content, r"restore_migration_bundle\.ps1")

    def test_env_examples_document_runtime_ports_and_frontend_api_base(self):
        root_env = self._read(".env.example")
        frontend_env = self._read("templates/front/admin/.env.example")

        self.assertRegex(root_env, r"APP_BACKEND_HOST=")
        self.assertRegex(root_env, r"APP_BACKEND_PORT=")
        self.assertRegex(root_env, r"APP_FRONTEND_PORT=")
        self.assertRegex(root_env, r"VITE_API_BASE_URL=")
        self.assertRegex(frontend_env, r"VITE_API_BASE_URL=")


if __name__ == "__main__":
    unittest.main()

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

    def test_backend_start_script_uses_env_file_and_wsgi_runner(self):
        content = self._read("bin/start_backend.ps1")
        self.assertIn(".env", content)
        self.assertRegex(content, r"run_backend_wsgi\.py")
        self.assertRegex(content, r"APP_BACKEND_PORT")

    def test_project_start_script_bootstraps_backend_and_frontend(self):
        content = self._read("bin/start_project.ps1")
        self.assertRegex(content, r"start_backend\.ps1")
        self.assertRegex(content, r"npm\s+run\s+serve")
        self.assertRegex(content, r"APP_FRONTEND_PORT")

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

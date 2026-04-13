import os
import re
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DockerSetupTest(unittest.TestCase):
    def _read(self, relative_path):
        path = os.path.join(PROJECT_ROOT, relative_path)
        with open(path, encoding="utf-8") as file_obj:
            return file_obj.read()

    def test_backend_dockerfile_exists_and_installs_torch(self):
        dockerfile_path = os.path.join(PROJECT_ROOT, "Dockerfile.backend")
        self.assertTrue(os.path.exists(dockerfile_path))
        content = self._read("Dockerfile.backend")
        self.assertRegex(content, r"pip\s+install.*torch")

    def test_compose_defines_backend_service_for_torch_runtime(self):
        content = self._read("docker-compose.yml")
        self.assertRegex(content, r"(?m)^  backend:\s*$")
        self.assertRegex(content, r"image:\s*mysql:8\.0")
        self.assertRegex(content, r"DB_HOST:\s*(?:db|\$\{DB_HOST:-db\})")
        self.assertRegex(content, r"REDIS_HOST:\s*(?:redis|\$\{REDIS_HOST:-redis\})")
        self.assertRegex(content, r"8080:8080")


if __name__ == "__main__":
    unittest.main()

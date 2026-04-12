import os
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from util.configread import config_read, redis_config_read


class ConfigReadTest(unittest.TestCase):
    def test_config_read_prefers_dotenv_values_when_process_env_missing(self):
        with tempfile.TemporaryDirectory() as tempdir:
            config_path = os.path.join(tempdir, "config.ini")
            env_path = os.path.join(tempdir, ".env")
            with open(config_path, "w", encoding="utf-8") as config_file:
                config_file.write(
                    textwrap.dedent(
                        """
                        [sql]
                        type = mysql
                        host = 127.0.0.1
                        port = 3306
                        user = root
                        passwd = 123456
                        db = diandong5k56la1f
                        charset = utf8
                        hasHadoop = spark
                        """
                    ).strip()
                )
            with open(env_path, "w", encoding="utf-8") as env_file:
                env_file.write(
                    textwrap.dedent(
                        """
                        DB_HOST=mysql
                        DB_PORT=3307
                        DB_NAME=ev_demo
                        HAS_HADOOP=none
                        """
                    ).strip()
                )

            with patch.dict(os.environ, {}, clear=True):
                values = config_read(config_path)

            self.assertEqual(values[1], "mysql")
            self.assertEqual(values[2], 3307)
            self.assertEqual(values[5], "ev_demo")
            self.assertEqual(values[7], "none")

    def test_redis_config_read_prefers_dotenv_values_when_process_env_missing(self):
        with tempfile.TemporaryDirectory() as tempdir:
            config_path = os.path.join(tempdir, "config.ini")
            env_path = os.path.join(tempdir, ".env")
            with open(config_path, "w", encoding="utf-8") as config_file:
                config_file.write(
                    textwrap.dedent(
                        """
                        [sql]
                        type = mysql
                        host = 127.0.0.1
                        port = 3306
                        user = root
                        passwd = 123456
                        db = diandong5k56la1f
                        charset = utf8
                        hasHadoop = spark

                        [redis]
                        host = 127.0.0.1
                        port = 6379
                        passwd = 123456
                        """
                    ).strip()
                )
            with open(env_path, "w", encoding="utf-8") as env_file:
                env_file.write(
                    textwrap.dedent(
                        """
                        REDIS_HOST=redis
                        REDIS_PORT=6380
                        REDIS_PASSWORD=redispass
                        REDIS_DB=2
                        """
                    ).strip()
                )

            with patch.dict(os.environ, {}, clear=True):
                values = redis_config_read(config_path)

            self.assertEqual(values[0], "redis")
            self.assertEqual(values[1], 6380)
            self.assertEqual(values[2], "redispass")
            self.assertEqual(values[3], 2)


if __name__ == "__main__":
    unittest.main()

import argparse
import sys
from pathlib import Path

import mysql.connector
from mysql.connector import Error


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from util.configread import config_read  # noqa: E402


DEFAULT_CONFIG = REPO_ROOT / "config.ini"
DEFAULT_SQL_FILE = REPO_ROOT / "db" / "diandong5k56la1f.sql"
SOURCE_DATABASE_NAME = "diandong5k56la1f"


def parse_args():
    parser = argparse.ArgumentParser(description="Bootstrap the local MySQL database for Windows development.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to config.ini")
    parser.add_argument("--sql-file", default=str(DEFAULT_SQL_FILE), help="Path to the base SQL dump")
    return parser.parse_args()


def load_db_settings(config_path):
    # DB_NAME 等运行时配置优先从 .env 读取，不足时再回退 config.ini。
    dbtype, host, port, user, password, db_name, charset, _ = config_read(str(config_path))
    if dbtype != "mysql":
        raise RuntimeError("当前自举脚本只支持 MySQL 本地环境。")
    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "db_name": db_name,
        "charset": charset or "utf8mb4",
    }


def connect_mysql(settings):
    return mysql.connector.connect(
        host=settings["host"],
        port=settings["port"],
        user=settings["user"],
        password=settings["password"],
        charset=settings["charset"],
        use_unicode=True,
        autocommit=True,
    )


def database_exists(connection, db_name):
    cursor = connection.cursor()
    try:
        cursor.execute("SHOW DATABASES LIKE %s", (db_name,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def rewrite_dump_database_name(sql_text, target_name):
    # 基础 dump 内部包含 DROP DATABASE / CREATE DATABASE / USE 语句，需要替换到当前 DB_NAME。
    rewritten = sql_text.replace(f"`{SOURCE_DATABASE_NAME}`", f"`{target_name}`")
    rewritten = rewritten.replace(f"Database: {SOURCE_DATABASE_NAME}", f"Database: {target_name}")
    return rewritten


def execute_sql_script(connection, sql_text):
    for result in connection.cmd_query_iter(sql_text):
        if isinstance(result, dict) and result.get("columns"):
            connection.get_rows()


def bootstrap_database(settings, sql_file):
    sql_text = sql_file.read_text(encoding="utf-8")
    sql_text = rewrite_dump_database_name(sql_text, settings["db_name"])

    with connect_mysql(settings) as connection:
        if database_exists(connection, settings["db_name"]):
            print(f"数据库 `{settings['db_name']}` 已存在，跳过基础 SQL 导入。", flush=True)
            return False

        print(
            f"数据库 `{settings['db_name']}` 不存在，正在基于 `{sql_file.name}` 执行首次导入...",
            flush=True,
        )
        execute_sql_script(connection, sql_text)
        print(f"数据库 `{settings['db_name']}` 基础导入完成。", flush=True)
        return True


def main():
    args = parse_args()
    config_path = Path(args.config).resolve()
    sql_file = Path(args.sql_file).resolve()

    if not config_path.exists():
        raise SystemExit(f"未找到配置文件：{config_path}")
    if not sql_file.exists():
        raise SystemExit(f"未找到基础 SQL 文件：{sql_file}")

    try:
        settings = load_db_settings(config_path)
        bootstrap_database(settings, sql_file)
    except Error as exc:
        raise SystemExit(
            "本地 MySQL 初始化失败，请确认 MySQL 服务已启动，且 `.env` / `config.ini` 中的账号密码正确。\n"
            f"详细错误：{exc}"
        ) from exc
    except Exception as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()

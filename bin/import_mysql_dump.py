import argparse
from pathlib import Path

import mysql.connector


def parse_args():
    parser = argparse.ArgumentParser(description="Import a MySQL dump without requiring mysql.exe.")
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", default="")
    parser.add_argument("--database", required=True)
    parser.add_argument("--charset", default="utf8mb4")
    parser.add_argument("--input", required=True)
    return parser.parse_args()


def quote_identifier(value):
    return "`" + value.replace("`", "``") + "`"


def connect(args, database=None):
    return mysql.connector.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password or None,
        database=database,
        charset=args.charset,
        use_unicode=True,
        autocommit=True,
    )


def execute_sql_script(connection, sql_text):
    for result in connection.cmd_query_iter(sql_text):
        if isinstance(result, dict) and result.get("columns"):
            connection.get_rows()


def import_database(args):
    dump_path = Path(args.input).resolve()
    if not dump_path.exists():
        raise SystemExit(f"Database dump not found: {dump_path}")

    collation = "utf8mb4_unicode_ci" if args.charset == "utf8mb4" else "utf8_general_ci"
    create_sql = (
        f"CREATE DATABASE IF NOT EXISTS {quote_identifier(args.database)} "
        f"DEFAULT CHARACTER SET {args.charset} COLLATE {collation};"
    )

    with connect(args) as connection:
        execute_sql_script(connection, create_sql)

    sql_text = dump_path.read_text(encoding="utf-8")
    with connect(args, database=args.database) as connection:
        execute_sql_script(connection, sql_text)


def main():
    import_database(parse_args())


if __name__ == "__main__":
    main()

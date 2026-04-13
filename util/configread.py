#coding:utf-8
import os
from configparser import ConfigParser


def _load_env_file(file_path):
    env_values = {}
    if not file_path or not os.path.exists(file_path):
        return env_values

    with open(file_path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_values[key.strip()] = value.strip().strip('"').strip("'")
    return env_values


def _load_runtime_env(config_path):
    config_dir = os.path.dirname(os.path.abspath(config_path))
    candidates = [
        os.path.join(config_dir, ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    env_values = {}
    for candidate in candidates:
        if os.path.exists(candidate):
            env_values.update(_load_env_file(candidate))
    return env_values


def _get_setting(env_values, env_key, fallback):
    return os.getenv(env_key, env_values.get(env_key, fallback))


def _normalize_mysql_charset(charset):
    normalized = (charset or "").strip().lower()
    if normalized in {"utf8", "utf-8", "utf8mb3"}:
        return "utf8mb4"
    return charset


def config_read(filePath:str):
    cfg=ConfigParser()
    cfg.read(filePath, encoding="utf-8-sig")
    env_values = _load_runtime_env(filePath)
    if "sql" in cfg.sections():
        dbType=_get_setting(env_values, "DB_TYPE", cfg.get('sql','type'))
        host=_get_setting(env_values, "DB_HOST", cfg.get('sql','host'))
        port=int(_get_setting(env_values, "DB_PORT", cfg.getint('sql','port')))
        user=_get_setting(env_values, "DB_USER", cfg.get('sql','user'))
        passwd=_get_setting(env_values, "DB_PASSWORD", cfg.get('sql','passwd'))
        dbName=_get_setting(env_values, "DB_NAME", cfg.get('sql','db'))
        charset=_normalize_mysql_charset(_get_setting(env_values, "DB_CHARSET", cfg.get('sql','charset')))
        hasHadoop=_get_setting(env_values, "HAS_HADOOP", cfg.get('sql','hasHadoop'))
        return dbType,host,port,user,passwd,dbName,charset,hasHadoop
    else:
        return None,None,None,None,None,None,None,None


def redis_config_read(filePath:str):
    cfg = ConfigParser()
    cfg.read(filePath, encoding="utf-8-sig")
    env_values = _load_runtime_env(filePath)
    if "redis" in cfg.sections():
        host = _get_setting(env_values, "REDIS_HOST", cfg.get("redis", "host"))
        port = int(_get_setting(env_values, "REDIS_PORT", cfg.getint("redis", "port")))
        password = _get_setting(env_values, "REDIS_PASSWORD", cfg.get("redis", "passwd"))
        db = int(_get_setting(env_values, "REDIS_DB", 1))
        return host, port, password, db
    return None, None, None, None

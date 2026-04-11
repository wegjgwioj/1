@echo off
if not exist .env (
  copy .env.example .env >nul
)
docker compose up -d db
if exist .\.venv\Scripts\python.exe (
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
  .\.venv\Scripts\python.exe manage.py migrate --fake-initial
  .\.venv\Scripts\python.exe manage.py sync_feature_schema
) else (
  pip install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
  python manage.py migrate --fake-initial
  python manage.py sync_feature_schema
)
pause

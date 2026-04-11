@echo off
if not exist .env (
  copy .env.example .env >nul
)
docker compose up -d db
if exist .\.venv\Scripts\python.exe (
  .\.venv\Scripts\python.exe manage.py sync_feature_schema
) else (
  python manage.py sync_feature_schema
)
pause

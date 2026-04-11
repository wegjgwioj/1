@echo off
if not exist .env (
  copy .env.example .env >nul
)
docker compose up -d db
if exist .\.venv\Scripts\python.exe (
  .\.venv\Scripts\python.exe manage.py prepare_demo_data
) else (
  python manage.py prepare_demo_data
)
pause

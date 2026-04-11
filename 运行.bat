@echo off
if exist .\.venv\Scripts\python.exe (
  .\.venv\Scripts\python.exe manage.py runserver --insecure 0.0.0.0:8080 --noreload
) else (
  python manage.py runserver --insecure 0.0.0.0:8080 --noreload
)
pause

#!/usr/bin/env python
import os
import sys
import threading
import webbrowser

def open_browser():
    # 仅在显式开启时才自动打开浏览器，避免开发/测试过程被强制打断。
    should_open = os.getenv("OPEN_ADMIN_ON_RUNSERVER", "").lower() in {"1", "true", "yes"}
    is_runserver = len(sys.argv) > 1 and sys.argv[1] == "runserver"
    if should_open and is_runserver:
        threading.Timer(1, webbrowser.open, args=['http://localhost:8080/admin/dist/index.html']).start()

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj2.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    open_browser()
    execute_from_command_line(sys.argv)

import argparse
import os
from wsgiref.simple_server import make_server


def main():
    parser = argparse.ArgumentParser(description="Run the Django backend with a stable WSGI server.")
    parser.add_argument("--host", default=os.getenv("APP_BACKEND_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("APP_BACKEND_PORT", "8082")))
    args = parser.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj2.settings")

    import django

    django.setup()

    from dj2.wsgi import application

    host = args.host
    port = args.port
    with make_server(host, port, application) as httpd:
        print(f"WSGI server listening on http://{host}:{port}", flush=True)
        httpd.serve_forever()


if __name__ == "__main__":
    main()

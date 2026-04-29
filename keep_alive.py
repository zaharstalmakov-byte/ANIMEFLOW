"""Keep-alive listener for free hostings (UptimeRobot / cron-job.org pinger).

Spawns a tiny HTTP server in a background thread that always replies 200 OK,
so an external uptime pinger can hit it every few minutes and prevent the
main FastAPI app from being put to sleep on free tiers.

Usage (e.g. from your run script or main.py)::

    from keep_alive import keep_alive
    keep_alive()  # call once at startup

Set ``KEEP_ALIVE_PORT`` env var to change the listen port (default 8080).

Implemented with the stdlib ``http.server`` so it has zero extra dependencies
(works on bare Python 3.8 without Flask).
"""
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 — name dictated by stdlib API
        body = b"AnimeFlow is alive"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args, **_kwargs):  # silence default request logs
        return


_started = False


def _serve(port: int) -> None:
    server = HTTPServer(("0.0.0.0", port), _Handler)
    server.serve_forever()


def keep_alive(port: int = None) -> None:
    """Start the keep-alive HTTP server in a daemon thread (idempotent)."""
    global _started
    if _started:
        return
    p = int(port if port is not None else os.environ.get("KEEP_ALIVE_PORT", "8080"))
    t = threading.Thread(target=_serve, args=(p,), daemon=True, name="keep-alive")
    t.start()
    _started = True


if __name__ == "__main__":
    keep_alive()
    import time
    print("[keep_alive] listening on port {}".format(
        os.environ.get("KEEP_ALIVE_PORT", "8080")
    ))
    while True:
        time.sleep(3600)

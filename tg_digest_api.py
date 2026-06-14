"""
Minimal HTTP server serving /data/sources/ markdown files.
Protected by API_SECRET env var.
"""
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

log = logging.getLogger(__name__)

SOURCES_DIR = os.environ.get("SOURCES_DIR", "/data/sources")
API_SECRET = os.environ.get("API_SECRET", "")
PORT = int(os.environ.get("PORT", "8080"))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default access log

    def _check_auth(self) -> bool:
        if not API_SECRET:
            return True
        return self.headers.get("X-API-Key") == API_SECRET

    def do_GET(self):
        if not self._check_auth():
            self.send_response(401)
            self.end_headers()
            return

        path = self.path.lstrip("/")

        # GET /list → JSON array of available .md filenames
        if path == "list":
            src = Path(SOURCES_DIR)
            files = sorted(f.name for f in src.glob("*.md")) if src.exists() else []
            body = json.dumps(files).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
            return

        # GET /sources/<filename.md> → file content
        if path.startswith("sources/") and path.endswith(".md"):
            filename = os.path.basename(path)
            filepath = os.path.join(SOURCES_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.send_header("Content-Length", len(body))
                self.end_headers()
                self.wfile.write(body)
                return

        self.send_response(404)
        self.end_headers()


def start_server():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    log.info("API server started on port %d", PORT)
    server.serve_forever()

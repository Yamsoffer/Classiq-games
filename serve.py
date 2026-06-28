#!/usr/bin/env python3
"""
Tiny zero-dependency local dev server for Classiq-games.

Serves the project directory over http://localhost:<port> and live-reloads the
browser whenever any .html / .css / .js file changes — so you can edit Albert
and just watch the page update.

Usage:
    python3 serve.py                      # serve + open Albert/albert.html
    python3 serve.py index.html           # open a specific page
    python3 serve.py --port 9000 q-circuit.html
    python3 serve.py --no-open            # don't auto-open a browser
"""
import argparse
import http.server
import os
import socketserver
import threading
import time
import webbrowser
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
WATCH_EXT = (".html", ".css", ".js")

# Injected into every .html response — polls the server and reloads on change.
LIVERELOAD = """
<script>
(function () {
  let last = null;
  async function check() {
    try {
      const r = await fetch('/__livecheck', { cache: 'no-store' });
      const t = await r.text();
      if (last !== null && t !== last) location.reload();
      last = t;
    } catch (e) { /* server restarting — ignore */ }
  }
  setInterval(check, 700);
  check();
})();
</script>
"""


def latest_mtime():
    """Newest modification time across watched files in the project."""
    newest = 0.0
    for dirpath, _dirs, files in os.walk(ROOT):
        if os.path.basename(dirpath).startswith('.'):
            continue
        for f in files:
            if f.endswith(WATCH_EXT):
                try:
                    newest = max(newest, os.path.getmtime(os.path.join(dirpath, f)))
                except OSError:
                    pass
    return newest


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        # never cache during development
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/__livecheck":
            body = str(latest_mtime()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Inject the live-reload snippet into HTML pages.
        fs_path = self.translate_path(self.path)
        if os.path.isdir(fs_path):
            fs_path = os.path.join(fs_path, "index.html")
        if fs_path.endswith(".html") and os.path.isfile(fs_path):
            with open(fs_path, "rb") as fh:
                html = fh.read().decode("utf-8", "replace")
            snippet = LIVERELOAD
            if "</body>" in html:
                html = html.replace("</body>", snippet + "</body>", 1)
            else:
                html += snippet
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        super().do_GET()

    def log_message(self, fmt, *args):
        # quieter: skip the noisy livecheck polls
        if "__livecheck" in (args[0] if args else ""):
            return
        super().log_message(fmt, *args)


def main():
    ap = argparse.ArgumentParser(description="Local dev server with live reload")
    ap.add_argument("page", nargs="?", default="Albert/albert.html",
                    help="page to open (default: Albert/albert.html)")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-open", action="store_true", help="don't open a browser")
    args = ap.parse_args()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", args.port), Handler) as httpd:
        url = f"http://localhost:{args.port}/{args.page.lstrip('/')}"
        print(f"\n  Classiq-games dev server")
        print(f"  → serving {ROOT}")
        print(f"  → {url}")
        print(f"  live-reload ON · Ctrl+C to stop\n")
        if not args.no_open:
            threading.Timer(0.6, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  stopped.")


if __name__ == "__main__":
    main()

"""Loopback-only preview with the actual wiki Content Security Policy."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
POLICY = re.search(r'Content-Security-Policy "([^"]+)"', (ROOT/'wiki/nginx.conf').read_text()).group(1)


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Content-Security-Policy', POLICY)
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8773), partial(Handler, directory=str(ROOT/'wiki/dist'))).serve_forever()

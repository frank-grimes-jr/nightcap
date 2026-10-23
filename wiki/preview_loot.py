"""Loopback-only wiki preview with public loot data and production CSP."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re

HERE=Path(__file__).resolve().parent
DATA=HERE.parent/'artifacts/wiki-loot/preview/loot-data'

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(HERE/'dist'),**kwargs)
    def translate_path(self,path):
        path=unquote(urlsplit(path).path)
        if path.startswith('/loot-data/'):
            relative=path[len('/loot-data/'):]
            if re.fullmatch(r'(current/index\.json|[a-f0-9]{16}/(?:index\.json|item-[1-9][0-9]{0,6}\.json))',relative):
                return str(DATA/relative)
            return str(HERE/'dist/__not_public__')
        return super().translate_path(path)
    def end_headers(self):
        self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()

if __name__=='__main__': ThreadingHTTPServer(('127.0.0.1',8769),Handler).serve_forever()

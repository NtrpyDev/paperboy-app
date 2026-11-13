"""A local HTTP server that lays out one explainer the way the content base does:
the explainer folder at /papers/x/ and the kit folder at /kit/."""
import contextlib
import mimetypes
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

PAPER_PATH = "/papers/x/"

TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".ttf": "font/ttf",
}


def _resolve(roots: dict[str, Path], url_path: str) -> Path | None:
    path = unquote(urlsplit(url_path).path)
    for prefix, root in roots.items():
        if not path.startswith(prefix):
            continue
        rest = path[len(prefix):]
        target = (root / rest).resolve()
        if target != root and root not in target.parents:
            return None
        if target.is_dir():
            target = target / "index.html"
        return target if target.is_file() else None
    return None


@contextlib.contextmanager
def serve(explainer: Path, kit: Path):
    """Serve on a free port on 127.0.0.1. Yields the explainer's URL."""
    roots = {PAPER_PATH: explainer.resolve(), "/kit/": kit.resolve()}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            target = _resolve(roots, self.path)
            if target is None:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            body = target.read_bytes()
            kind = TYPES.get(target.suffix.lower()) or mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}{PAPER_PATH}"
    finally:
        server.shutdown()
        server.server_close()

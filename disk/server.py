"""Disk Space. Read-only. Does not import any other FAFO tool."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

PORT = 18771
ROOT = Path(__file__).resolve().parent


def scan(folder: str, limit: int = 5000) -> dict:
    base = Path(folder).expanduser()
    if not base.is_dir():
        return {"error": "That folder was not found."}
    total = 0
    count = 0
    folders: dict[str, int] = {}
    largest: list[tuple[int, str]] = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [name for name in dirnames if name not in {".git", "node_modules", "$RECYCLE.BIN"}]
        for name in filenames:
            if count >= limit:
                break
            path = Path(dirpath) / name
            try:
                size = path.stat().st_size
            except OSError:
                continue
            total += size
            count += 1
            rel = str(path.relative_to(base))
            top = rel.split(os.sep, 1)[0]
            folders[top] = folders.get(top, 0) + size
            largest.append((size, rel))
        if count >= limit:
            break
    largest.sort(reverse=True)
    folder_rows = sorted(({ "name": name, "size": size } for name, size in folders.items()), key=lambda row: row["size"], reverse=True)
    return {
        "total": total,
        "count": count,
        "capped": count >= limit,
        "folders": folder_rows[:12],
        "files": [{"name": name, "size": size} for size, name in largest[:20]],
    }


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _page(self) -> None:
        page = (ROOT / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/":
            self._page()
            return
        self._json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/scan":
            self._json(404, {"error": "Not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "Bad request"})
            return
        self._json(200, scan(str(body.get("path") or "")))

    def log_message(self, fmt: str, *args) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

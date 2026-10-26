"""Reports and Logs. Reads one text file. Does not write it and does not import other tools."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 18775
ROOT = Path(__file__).resolve().parent


def read_log(path: str) -> dict:
    file = Path(path).expanduser()
    if not file.is_file():
        return {"error": "That file was not found."}
    if file.stat().st_size > 8_000_000:
        return {"error": "That file is larger than 8 MB. Open a smaller log."}
    try:
        text = file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"error": "Could not read that file."}
    lines = text.splitlines()[:4000]
    return {"name": file.name, "lines": lines}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == "/":
            self._send(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        self._send(404, b"{}", "application/json")

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/api/open":
            self._send(404, b"{}", "application/json")
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send(400, b'{"error":"Bad request"}', "application/json")
            return
        self._send(200, json.dumps(read_log(str(body.get("path") or ""))).encode(), "application/json")

    def log_message(self, fmt: str, *args) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

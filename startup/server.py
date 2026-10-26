"""Startup List. Read-only. Cannot enable or disable startup items."""
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 18774
ROOT = Path(__file__).resolve().parent


def items() -> dict:
    if os.name != "nt":
        return {"items": [], "error": "Startup programs are only listed on Windows. This tool cannot turn them off."}
    script = (
        "Get-CimInstance Win32_StartupCommand | "
        "Select-Object Name, Command, Location | ConvertTo-Json -Depth 3"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True)
    if result.returncode != 0:
        return {"items": [], "error": "Could not read startup programs."}
    try:
        data = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return {"items": [], "error": "The startup reply was not readable."}
    rows = data if isinstance(data, list) else [data]
    return {
        "items": [
            {"name": str(row.get("Name") or ""), "command": str(row.get("Command") or ""), "location": str(row.get("Location") or "")}
            for row in rows
        ]
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/api/list":
            self._send(200, json.dumps(items()).encode(), "application/json")
            return
        if path == "/":
            self._send(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        self._send(404, b"{}", "application/json")

    def log_message(self, fmt: str, *args) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

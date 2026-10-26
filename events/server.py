"""Event Viewer. Read-only. Does not clear logs and does not import other tools."""
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 18773
ROOT = Path(__file__).resolve().parent


def recent() -> dict:
    if os.name != "nt":
        return {"events": [], "error": "The Windows event log is only available on Windows."}
    script = (
        "Get-WinEvent -LogName System -MaxEvents 80 -ErrorAction SilentlyContinue | "
        "Select-Object TimeCreated, LevelDisplayName, ProviderName, Id, Message | "
        "ConvertTo-Json -Depth 3"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True)
    if result.returncode != 0:
        return {"events": [], "error": "Could not read the event log."}
    try:
        data = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return {"events": [], "error": "The event log reply was not readable."}
    rows = data if isinstance(data, list) else [data]
    events = []
    for row in rows:
        events.append({
            "time": str(row.get("TimeCreated") or ""),
            "level": str(row.get("LevelDisplayName") or ""),
            "source": str(row.get("ProviderName") or ""),
            "id": str(row.get("Id") or ""),
            "message": str(row.get("Message") or "")[:400],
        })
    return {"events": events}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/api/recent":
            self._send(200, json.dumps(recent()).encode(), "application/json")
            return
        if path == "/":
            self._send(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        self._send(404, b"{}", "application/json")

    def log_message(self, fmt: str, *args) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

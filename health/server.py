"""PC Health. Read-only snapshot. Does not import any other FAFO tool."""
import json
import os
import shutil
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 18772
ROOT = Path(__file__).resolve().parent


def snapshot() -> dict:
    mem_total = 0
    mem_used = 0
    if os.name != "nt":
        try:
            info = {}
            for line in Path("/proc/meminfo").read_text().splitlines():
                key, _, rest = line.partition(":")
                info[key] = int(rest.strip().split()[0]) * 1024
            mem_total = info.get("MemTotal", 0)
            mem_used = mem_total - info.get("MemAvailable", 0)
        except OSError:
            pass
        uptime = 0
        try:
            uptime = int(float(Path("/proc/uptime").read_text().split()[0]))
        except OSError:
            pass
    else:
        uptime = int(time.time())
    disks = []
    roots = ["C:\\", "D:\\"] if os.name == "nt" else ["/"]
    for name in roots:
        if not os.path.exists(name):
            continue
        usage = shutil.disk_usage(name)
        disks.append({"name": name, "used": usage.used, "total": usage.total})
    return {
        "host": os.environ.get("COMPUTERNAME") or os.uname().nodename,
        "cpuCount": os.cpu_count() or 0,
        "memUsed": mem_used,
        "memTotal": mem_total,
        "uptimeSec": uptime if os.name != "nt" else 0,
        "disks": disks,
        "windows": os.name == "nt",
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == "/api/snapshot":
            self._send(200, json.dumps(snapshot()).encode(), "application/json")
            return
        if self.path.split("?", 1)[0] == "/":
            self._send(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        self._send(404, b"{}", "application/json")

    def log_message(self, fmt: str, *args) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

"""FAFO Toolbox launcher. Installs or removes one module after confirm=true. Does not import module code."""
import json
import os
import shutil
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 18770
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
INSTALL_ROOT = Path(os.environ.get("FAFO_INSTALL_ROOT") or (r"C:\_git\FAFO" if os.name == "nt" else "/tmp/FAFO"))
CATALOG = json.loads((ROOT / "catalog.json").read_text())


def installed() -> list[dict]:
    found = []
    if not INSTALL_ROOT.is_dir():
        return found
    for child in INSTALL_ROOT.iterdir():
        marker = child / "module.json"
        if not marker.is_file():
            continue
        try:
            meta = json.loads(marker.read_text())
        except json.JSONDecodeError:
            continue
        found.append({"id": meta.get("id") or child.name, "name": meta.get("name") or child.name, "path": str(child)})
    return found


def install(module_id: str, confirm: bool) -> dict:
    if confirm is not True:
        return {"error": "Confirmation is required."}
    meta = next((item for item in CATALOG if item["id"] == module_id and item.get("ready")), None)
    if not meta:
        return {"error": "That tool is not available to install."}
    source = REPO / meta["folder"]
    marker = source / "module.json"
    if not marker.is_file():
        return {"error": "That tool is missing from this repo."}
    dest = INSTALL_ROOT / meta["folder"]
    if dest.exists():
        return {"ok": True, "path": str(dest), "already": True}
    INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest)
    return {"ok": True, "path": str(dest)}


def remove(module_id: str, confirm: bool) -> dict:
    if confirm is not True:
        return {"error": "Confirmation is required."}
    meta = next((item for item in CATALOG if item["id"] == module_id), None)
    if not meta:
        return {"error": "Unknown tool."}
    dest = (INSTALL_ROOT / meta["folder"]).resolve()
    root = INSTALL_ROOT.resolve()
    if dest == root or root not in dest.parents:
        return {"error": "Refusing to remove that path."}
    marker = dest / "module.json"
    if not marker.is_file():
        return {"error": "That tool is not installed."}
    try:
        current = json.loads(marker.read_text())
    except json.JSONDecodeError:
        return {"error": "That install is not readable."}
    if current.get("id") != module_id:
        return {"error": "Refusing to remove a folder that is not this tool."}
    shutil.rmtree(dest)
    return {"ok": True}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/":
            page = (ROOT / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
            return
        if path == "/api/catalog":
            self._send(200, {"modules": CATALOG, "installed": installed()})
            return
        self._send(404, {"error": "Not found"})

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "Bad request"})
            return
        module_id = str(body.get("id") or "")
        confirm = body.get("confirm") is True
        if path == "/api/install":
            self._send(200, install(module_id, confirm))
            return
        if path == "/api/remove":
            self._send(200, remove(module_id, confirm))
            return
        self._send(404, {"error": "Not found"})

    def log_message(self, fmt: str, *args) -> None:
        return


if __name__ == "__main__":
    if os.environ.get("FAFO_PULL") == "1" and (REPO / ".git").is_dir():
        subprocess.run(["git", "-C", str(REPO), "pull", "--ff-only"], check=False)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

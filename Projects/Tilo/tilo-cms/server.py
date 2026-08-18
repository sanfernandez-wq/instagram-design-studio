#!/usr/bin/env python3
"""
Servidor local para el CMS de Tilo Estudio (solo para desarrollo/pruebas).
No requiere instalar nada: usa únicamente la librería estándar de Python 3.

Cómo usarlo:
  1. Abrí la Terminal.
  2. cd a esta carpeta (tilo-cms).
  3. Ejecutá: python3 server.py
  4. Abrí en el navegador:
       - Sitio:  http://localhost:8788/tiloestudio.html
       - Panel:  http://localhost:8788/admin.html
  5. Para detener el servidor: Ctrl+C en la Terminal.
"""

import base64
import http.server
import json
import os
import re
import uuid
from urllib.parse import urlparse

PORT = 8788
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
IMG_DIR = os.path.join(ROOT, "assets")

# Cada colección: endpoint -> (archivo json, clave esperada, tipo: "list" o "dict")
COLLECTIONS = {
    "hero": (os.path.join(DATA_DIR, "hero.json"), "hero", "dict"),
    "services": (os.path.join(DATA_DIR, "services.json"), "services", "list"),
    "projects": (os.path.join(DATA_DIR, "projects.json"), "projects", "list"),
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, fmt, *args):
        # log más corto y legible
        print("  ", fmt % args)

    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            name = parsed.path[len("/api/"):]
            if name in COLLECTIONS:
                data_file, key, kind = COLLECTIONS[name]
                try:
                    with open(data_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._json(data)
                except FileNotFoundError:
                    self._json({key: [] if kind == "list" else {}})
                return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b""

        if parsed.path.startswith("/api/") and parsed.path != "/api/upload-image":
            name = parsed.path[len("/api/"):]
            if name in COLLECTIONS:
                data_file, key, kind = COLLECTIONS[name]
                try:
                    data = json.loads(body.decode("utf-8"))
                    if not isinstance(data, dict) or key not in data:
                        raise ValueError(f"Formato inválido: se esperaba {{ {key}: ... }}")
                    if kind == "list" and not isinstance(data[key], list):
                        raise ValueError(f"Formato inválido: se esperaba {{ {key}: [...] }}")
                    if kind == "dict" and not isinstance(data[key], dict):
                        raise ValueError(f"Formato inválido: se esperaba {{ {key}: {{...}} }}")
                    os.makedirs(os.path.dirname(data_file), exist_ok=True)
                    with open(data_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    self._json({"ok": True})
                except Exception as e:
                    self._json({"ok": False, "error": str(e)}, status=400)
                return

        if parsed.path == "/api/upload-image":
            try:
                data = json.loads(body.decode("utf-8"))
                data_url = data.get("dataUrl", "")
                prefix = re.sub(r"[^a-zA-Z0-9_-]", "", data.get("prefix", "img")) or "img"
                m = re.match(r"^data:image/(\w+);base64,(.*)$", data_url, re.DOTALL)
                if not m:
                    raise ValueError("La imagen no tiene un formato válido (data URL esperada).")
                ext = m.group(1).lower().replace("jpeg", "jpg")
                if ext not in ("jpg", "png", "webp", "gif"):
                    ext = "jpg"
                raw = base64.b64decode(m.group(2))
                os.makedirs(IMG_DIR, exist_ok=True)
                fname = f"{prefix}-{uuid.uuid4().hex[:10]}.{ext}"
                with open(os.path.join(IMG_DIR, fname), "wb") as f:
                    f.write(raw)
                self._json({"ok": True, "path": f"assets/{fname}"})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, status=400)
            return

        self._json({"ok": False, "error": "not found"}, status=404)


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Servidor corriendo en http://localhost:{PORT}")
        print(f"  Sitio:  http://localhost:{PORT}/tiloestudio.html")
        print(f"  Panel:  http://localhost:{PORT}/admin.html")
        print("Presioná Ctrl+C para detenerlo.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")

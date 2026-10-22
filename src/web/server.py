"""Vigil Web Console server (Phase 7).

A dependency-free (stdlib-only) HTTP server that serves the console's static
surfaces and a small JSON API backed by the REAL pipeline — the same
``VigilPipeline`` + ``DemoAdapter`` the tests exercise. No fabricated data: the
scenario endpoints return exactly what the deterministic engine produces, and
each payload carries the honesty markers (``source``, ``simulated``) so the UI
can badge MODELED readings as MODELED.

Security: binds to 127.0.0.1 only (never 0.0.0.0) — the console is a local
operator surface, not a public server.

Run:
    python -m src.web.server            # serves on http://127.0.0.1:5176
    python -m src.web.server --port 8080

API:
    GET /api/scenarios          -> list of {id, title, mode} for the selector
    GET /api/scenario/<id>      -> full resolved result for one scenario
    GET /api/mesh               -> static mesh-node descriptors (for the panel)
    GET /                       -> Mission Control surface (static/index.html)
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from src.pipeline.ingest import DemoAdapter, VigilPipeline
from src.simulator.scenario_runner import load_scenarios

_STATIC_DIR = Path(__file__).with_name("static")
_HOST = "127.0.0.1"
_DEFAULT_PORT = 5176

# Static descriptors for the mesh panel. Honest real-vs-MODELED status per node:
# the console shows which organs are live-capable and which are MODELED here.
_MESH_NODES = [
    {"id": "ring", "name": "RING_PRO_2", "role": "perimeter eyes/ears",
     "status": "ADAPTER_READY", "mode": "live-capable (API/simulator)"},
    {"id": "bee", "name": "BEE_WEAR", "role": "resident bio-state",
     "status": "MODELED", "mode": "no device — honest simulated contract"},
    {"id": "firetv", "name": "FIRE_TV", "role": "deterrence actuator",
     "status": "ADAPTER_READY", "mode": "live-capable (Fire TV Stick)"},
    {"id": "echo", "name": "ECHO_BEDROOM", "role": "Alexa+ brain / voice",
     "status": "ADAPTER_READY", "mode": "live-capable (Echo + MCP)"},
    {"id": "phone", "name": "PHONE_A35", "role": "human CAD authorization",
     "status": "ADAPTER_READY", "mode": "live-capable (Android)"},
]


def _scenario_payload(scenario_id: str) -> dict:
    """Resolve one scenario through the real pipeline and enrich with fixture provenance."""
    pipeline = VigilPipeline(DemoAdapter())
    result = pipeline.process(scenario_id)
    catalog = load_scenarios()
    fixture = catalog[result.scenario_id]
    telem = DemoAdapter().telemetry(scenario_id)
    sig = telem.signals
    integrity = sig.integrity
    payload = result.as_dict()
    payload.update({
        "source": telem.source,
        "simulated": telem.simulated,
        "score": telem.score,
        "ingest": fixture.get("ingest", {}),
        "subject": fixture.get("subject"),
        "host_state": fixture.get("host_state"),
        "integrity": {
            "phi_m": integrity.phi_m, "phi_v": integrity.phi_v,
            "phi_a": integrity.phi_a, "phi_net": integrity.phi_net,
        } if integrity else None,
        "signals": {
            "weapon_detected": sig.weapon_detected,
            "masked_near_entry": sig.masked_near_entry,
            "breach_acoustics": sig.breach_acoustics,
            "distress_flag": sig.distress_flag,
            "corroboration_count": sig.corroboration_count(),
        },
    })
    return payload


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the console quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/scenarios":
                catalog = load_scenarios()
                self._json(200, [
                    {"id": s["id"], "title": s["title"], "mode": s["mode"]}
                    for s in catalog.values()
                ])
                return
            if path.startswith("/api/scenario/"):
                sid = path.rsplit("/", 1)[-1]
                self._json(200, _scenario_payload(sid))
                return
            if path == "/api/mesh":
                self._json(200, _MESH_NODES)
                return
            self._serve_static(path)
        except KeyError as exc:
            self._json(404, {"error": str(exc)})
        except Exception as exc:  # never leak a stack to the browser
            self._json(500, {"error": type(exc).__name__})

    def _serve_static(self, path: str) -> None:
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        target = (_STATIC_DIR / rel).resolve()
        # Path-traversal guard: must stay within the static dir.
        if _STATIC_DIR.resolve() not in target.parents and target != _STATIC_DIR.resolve():
            self._json(403, {"error": "forbidden"})
            return
        if not target.is_file():
            self._json(404, {"error": "not found"})
            return
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".svg": "image/svg+xml",
            ".json": "application/json; charset=utf-8",
        }.get(target.suffix, "application/octet-stream")
        self._send(200, target.read_bytes(), ctype)


def build_server(port: int = _DEFAULT_PORT) -> ThreadingHTTPServer:
    """Construct (but do not start) the console server bound to localhost."""
    return ThreadingHTTPServer((_HOST, port), _Handler)


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Amazon Vigil web console")
    parser.add_argument("--port", type=int, default=_DEFAULT_PORT)
    args = parser.parse_args()
    httpd = build_server(args.port)
    print(f"Vigil console on http://{_HOST}:{args.port}  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

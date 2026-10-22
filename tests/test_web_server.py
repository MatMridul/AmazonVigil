"""Tests for the web console server (src/web/server.py).

Proves the Mission Control surface is WIRED to the real pipeline: the API
endpoints return exactly what VigilPipeline produces (not hardcoded data), the
honesty markers travel through, and static assets serve with a path-traversal
guard. Boots the real ThreadingHTTPServer on an ephemeral localhost port.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from src.web.server import build_server


@pytest.fixture
def server():
    httpd = build_server(port=0)  # ephemeral port
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()
    httpd.server_close()


def _get(base, path):
    with urllib.request.urlopen(base + path, timeout=5) as r:
        return r.status, r.read()


def _expect_http_error(base, path):
    """Fetch expecting an HTTPError; drain+close its body so no socket leaks."""
    try:
        _get(base, path)
    except urllib.error.HTTPError as exc:
        try:
            exc.read()
        finally:
            exc.close()
        return exc.code
    raise AssertionError(f"expected HTTPError for {path}")


def test_binds_to_localhost_only(server):
    assert server.startswith("http://127.0.0.1:")


def test_scenarios_endpoint_lists_ten(server):
    status, body = _get(server, "/api/scenarios")
    assert status == 200
    data = json.loads(body)
    assert len(data) == 10
    assert all("id" in s and "title" in s and "mode" in s for s in data)


def test_scenario_endpoint_returns_real_pipeline_result(server):
    # Prowler (06) → L2 via masked-near-entry + breach acoustics (NOT lens tamper).
    status, body = _get(server, "/api/scenario/06_covert_entry_breach")
    assert status == 200
    d = json.loads(body)
    assert d["level"] == "L2_SUSPICIOUS"
    assert d["action"] == "WAKE_HOST_AND_DETER"
    assert d["simulated"] is True
    assert d["source"] == "demo"
    assert d["integrity"]["phi_v"] == 1.0  # optics intact; escalation is masked+breach
    assert d["signals"]["masked_near_entry"] is True
    assert d["signals"]["breach_acoustics"] is True
    assert d["signals"]["corroboration_count"] >= 2


def test_lens_tamper_collapses_optical_integrity(server):
    # Scenario 08 is the optical-tamper case: phi_v collapses to 0.0.
    status, body = _get(server, "/api/scenario/08_lens_tamper_breach")
    d = json.loads(body)
    assert d["integrity"]["phi_v"] == 0.0
    assert d["level"] == "L2_SUSPICIOUS"


def test_duress_scenario_has_empty_actuators_and_cad(server):
    status, body = _get(server, "/api/scenario/10_host_duress_armed_coercion")
    d = json.loads(body)
    assert d["level"] == "L3_CRITICAL"
    assert d["cad_staged"] is True
    assert d["permitted_actuators"] == []  # SILENT_DURESS silence invariant, end to end
    assert d["cad_sha256"] and len(d["cad_sha256"]) == 64


def test_unknown_scenario_is_404(server):
    assert _expect_http_error(server, "/api/scenario/does_not_exist") == 404


def test_mesh_endpoint_marks_bee_modeled(server):
    status, body = _get(server, "/api/mesh")
    nodes = {n["id"]: n for n in json.loads(body)}
    assert nodes["bee"]["status"] == "MODELED"
    assert nodes["echo"]["status"] == "ADAPTER_READY"


def test_static_index_served(server):
    status, body = _get(server, "/")
    assert status == 200
    assert b"VIGIL" in body


def test_phone_surface_served(server):
    status, body = _get(server, "/phone.html")
    assert status == 200
    assert b"NIGHTSTAND" in body or b"TRANSMIT 911" in body


def _post_json(base, path, obj):
    data = json.dumps(obj).encode("utf-8")
    req = urllib.request.Request(
        base + path, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, json.loads(r.read())


def test_disarm_correct_pin_disarms(server):
    status, d = _post_json(server, "/api/disarm", {"pin": "1234"})
    assert status == 200
    assert d["disarmed"] is True


def test_disarm_wrong_pin_rejected(server):
    status, d = _post_json(server, "/api/disarm", {"pin": "0000"})
    assert d["disarmed"] is False
    assert d["reason"] == "invalid PIN"


def test_disarm_malformed_pin_rejected(server):
    status, d = _post_json(server, "/api/disarm", {"pin": "12"})
    assert d["disarmed"] is False


def test_path_traversal_blocked(server):
    assert _expect_http_error(server, "/../server.py") in (403, 404)

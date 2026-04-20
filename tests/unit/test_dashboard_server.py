from __future__ import annotations

import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

from src.dashboard.server import make_dashboard_handler, render_dashboard_index, render_iteration_detail_index


def test_render_dashboard_index_contains_required_live_monitor_regions():
    html = render_dashboard_index(refresh_seconds=2.5)

    assert "Run Health Strip" in html
    assert "Iteration Timeline" in html
    assert "Selected Iteration Panel" in html
    assert "Recent Activity" in html
    assert "Artifact Availability" in html
    assert "Performance Trend" in html
    assert "Decision Summary" in html
    assert "drawdown" in html
    assert "turnover" in html
    assert "deflated_sr" in html
    assert "baseline delta" in html
    assert "open-detail-link" in html
    assert "formatDiagnosis" in html
    assert "fetch('/api/state'" in html
    assert "setInterval(loadDashboardState, 2500)" in html


def test_render_iteration_detail_index_contains_drilldown_regions():
    html = render_iteration_detail_index(2, refresh_seconds=1.5)

    assert "Iteration Detail" in html
    assert "iteration-detail-status" in html
    assert "Hypothesis diff" in html
    assert "Strategy diff" in html
    assert "Metric breakdown" in html
    assert "Decision reasoning" in html
    assert "Artifact References" in html
    assert "Log Excerpts" in html
    assert "formatDiagnosis" in html
    assert "vs previous iteration" in html
    assert "setInterval(loadIterationDetail, 1500)" in html


def test_dashboard_index_escapes_untrusted_strings_before_inner_html_rendering():
    html = render_dashboard_index()

    assert "const escapeHtml = value =>" in html
    assert "${escapeHtml(run.status)}" in html
    assert "${escapeHtml(run.run_id)}" in html
    assert "${escapeHtml(formatDiagnosis(diagnosis, run.stop_reason)).replaceAll('\\n', '<br>')}" in html
    assert "${escapeHtml(iteration.status)}" in html
    assert "${escapeHtml(iteration.decision)}" in html
    assert "${escapeHtml(nodeLabel(iteration))}" in html
    assert "${escapeHtml(text(log.excerpt).slice(0, 180))}" in html
    assert "${text(log.excerpt).slice(0, 180)}" not in html
    assert "replace(/[^a-z0-9_-]/g, \"-\")" in html


def test_dashboard_index_resets_selected_panel_when_no_iterations_render():
    html = render_dashboard_index()

    assert "resetSelectedPanel()" in html
    assert "No iteration selected." in html
    assert "No strategy change yet." in html
    assert "No metrics yet." in html
    assert "No decision yet." in html


def test_iteration_detail_escapes_artifact_and_log_strings_before_inner_html_rendering():
    html = render_iteration_detail_index(2)

    assert "const escapeHtml = value =>" in html
    assert "<td>${escapeHtml(item.name)}</td>" in html
    assert '<td class="muted">${escapeHtml(item.path)}</td>' in html
    assert "${escapeHtml(log.updated_at)}" in html
    assert '<span class="muted">${escapeHtml(log.path)}</span>' in html
    assert "<pre>${escapeHtml(log.excerpt)}</pre>" in html
    assert "${text(item.path)}" not in html
    assert "${text(log.excerpt)}" not in html


def test_iteration_detail_resets_missing_iteration_sections():
    html = render_iteration_detail_index(2)

    assert "resetMissingIterationDetail()" in html
    assert "No iteration selected." in html
    assert "No artifact references yet." in html
    assert "No logs yet." in html


def test_dashboard_handler_serves_index_and_observer_json(tmp_path):
    state_path = tmp_path / "experiments" / "autoresearch_state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps(
            {
                "run_id": "run-test",
                "status": "running",
                "current_iteration": 0,
                "active_iteration": None,
                "updated_at": "2026-04-20T00:00:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    handler = make_dashboard_handler(tmp_path, refresh_seconds=1.0)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address
        with urlopen(f"http://{host}:{port}/", timeout=5) as response:
            html = response.read().decode("utf-8")
            assert response.status == 200
            assert "Run Health Strip" in html

        with urlopen(f"http://{host}:{port}/api/state", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
            assert payload["run"]["run_id"] == "run-test"
            assert sorted(payload.keys()) == ["iterations", "ledger", "observed_at", "run", "sources"]

        with urlopen(f"http://{host}:{port}/iterations/1", timeout=5) as response:
            html = response.read().decode("utf-8")
            assert response.status == 200
            assert "Iteration Detail" in html
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

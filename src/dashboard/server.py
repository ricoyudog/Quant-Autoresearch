from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .observer import observe_dashboard_state


def render_dashboard_index(*, refresh_seconds: float = 3.0) -> str:
    """Render the read-only dashboard shell."""
    refresh_milliseconds = max(1, int(refresh_seconds * 1000))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Quant Autoresearch Live Monitor</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #090c10;
      --panel: rgba(17, 23, 31, 0.84);
      --panel-strong: rgba(25, 35, 46, 0.96);
      --line: rgba(141, 232, 255, 0.22);
      --ink: #e9f7ff;
      --muted: #90a8b5;
      --cyan: #56e4ff;
      --lime: #c6ff5c;
      --amber: #ffcc66;
      --red: #ff6b7a;
      --shadow: 0 22px 80px rgba(0, 0, 0, 0.45);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      min-height: 100vh;
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 18% 12%, rgba(86, 228, 255, 0.18), transparent 30rem),
        radial-gradient(circle at 82% 18%, rgba(198, 255, 92, 0.10), transparent 28rem),
        linear-gradient(135deg, #06080c 0%, #0d1218 54%, #11171f 100%);
      font-family: "Avenir Next", "Gill Sans", "Trebuchet MS", sans-serif;
      letter-spacing: 0.01em;
    }}
    main {{
      width: min(1500px, calc(100vw - 40px));
      margin: 0 auto;
      padding: 32px 0 44px;
    }}
    .masthead {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 24px;
      margin-bottom: 20px;
    }}
    h1 {{
      margin: 0;
      font-family: "Copperplate", "Avenir Next", sans-serif;
      font-size: clamp(2rem, 5vw, 4.8rem);
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    .eyebrow {{
      color: var(--cyan);
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.22em;
      text-transform: uppercase;
    }}
    .refresh {{
      color: var(--muted);
      text-align: right;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      font-size: 0.74rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(320px, 0.95fr) minmax(420px, 1.35fr) minmax(260px, 0.7fr);
      gap: 18px;
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 26px;
      background: var(--panel);
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    .panel h2, .panel h3 {{
      margin: 0;
      padding: 18px 20px 12px;
      font-size: 0.82rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--cyan);
      border-bottom: 1px solid var(--line);
    }}
    .panel-title-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .open-detail-link {{
      color: var(--lime);
      font-size: 0.68rem;
      text-decoration: none;
      letter-spacing: 0.12em;
    }}
    .health {{
      display: grid;
      grid-column: 1 / -1;
      grid-template-columns: repeat(6, minmax(130px, 1fr));
      gap: 1px;
      background: var(--line);
      margin-bottom: 18px;
    }}
    .health > div {{
      min-height: 104px;
      padding: 18px;
      background: var(--panel-strong);
    }}
    .label {{
      color: var(--muted);
      font-size: 0.72rem;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }}
    .value {{
      margin-top: 8px;
      font-size: clamp(1.05rem, 2vw, 1.7rem);
      font-weight: 800;
      word-break: break-word;
    }}
    .status-healthy, .status-busy, .status-kept {{ color: var(--lime); }}
    .status-waiting, .status-decision-pending, .status-evaluated {{ color: var(--amber); }}
    .status-stalled, .status-blocked, .status-failed {{ color: var(--red); }}
    .timeline-list {{
      display: grid;
      gap: 12px;
      padding: 18px;
      max-height: 670px;
      overflow: auto;
    }}
    .node {{
      width: 100%;
      padding: 16px;
      border: 1px solid rgba(255,255,255,0.10);
      border-radius: 18px;
      color: inherit;
      background: rgba(255,255,255,0.035);
      text-align: left;
      cursor: pointer;
    }}
    .node[aria-selected="true"] {{
      border-color: var(--cyan);
      background: linear-gradient(135deg, rgba(86, 228, 255, 0.18), rgba(198, 255, 92, 0.08));
    }}
    .node-title {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-weight: 800;
    }}
    .metric-row {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      margin-top: 14px;
    }}
    .metric {{
      padding: 10px;
      border-radius: 12px;
      background: rgba(0,0,0,0.22);
    }}
    .metric strong {{
      display: block;
      margin-top: 4px;
    }}
    .detail-section {{
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
    }}
    .detail-section:last-child {{ border-bottom: 0; }}
    pre {{
      white-space: pre-wrap;
      margin: 8px 0 0;
      font-family: "SFMono-Regular", "Menlo", monospace;
      font-size: 0.82rem;
    }}
    .support {{
      display: grid;
      gap: 18px;
    }}
    .support .panel div {{
      padding: 16px 18px;
      color: var(--muted);
      line-height: 1.5;
      white-space: pre-wrap;
    }}
    .empty {{
      padding: 22px;
      color: var(--muted);
    }}
    @media (max-width: 1120px) {{
      .grid {{ grid-template-columns: 1fr; }}
      .health {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
  </style>
</head>
<body>
  <main>
    <header class="masthead">
      <div>
        <div class="eyebrow">Read-only local cockpit</div>
        <h1>Research Monitor</h1>
      </div>
      <div class="refresh">Live refresh · <span id="refresh-rate">{refresh_seconds:g}s</span><br><span id="last-refresh">Booting</span></div>
    </header>

    <section class="panel health" aria-label="Run Health Strip" id="run-health-strip">
      <div><span class="label">Run Health Strip</span><div class="value">Loading</div></div>
    </section>

    <section class="grid">
      <aside class="panel">
        <h2>Iteration Timeline</h2>
        <div class="timeline-list" id="iteration-timeline"><div class="empty">Waiting for iterations…</div></div>
      </aside>

      <section class="panel" id="selected-iteration-panel">
        <h2 class="panel-title-row">Selected Iteration Panel <a class="open-detail-link" id="open-detail-link" href="#">Open detail page</a></h2>
        <div class="detail-section"><span class="label">Hypothesis diff</span><pre id="hypothesis-diff">No iteration selected.</pre></div>
        <div class="detail-section"><span class="label">Strategy diff</span><pre id="strategy-diff">No strategy change yet.</pre></div>
        <div class="detail-section"><span class="label">Metric breakdown</span><pre id="metric-breakdown">No metrics yet.</pre></div>
        <div class="detail-section"><span class="label">Decision reasoning</span><pre id="decision-reasoning">No decision yet.</pre></div>
      </section>

      <aside class="support">
        <section class="panel"><h3>Recent Activity</h3><div id="recent-activity">No logs yet.</div></section>
        <section class="panel"><h3>Artifact Availability</h3><div id="artifact-availability">No artifacts yet.</div></section>
        <section class="panel"><h3>Performance Trend</h3><div id="performance-trend">No ledger data yet.</div></section>
        <section class="panel"><h3>Decision Summary</h3><div id="decision-summary">No decisions yet.</div></section>
      </aside>
    </section>
  </main>
  <script>
    const refreshMs = {refresh_milliseconds};
    let selectedIteration = null;
    const text = value => value === null || value === undefined || value === "" ? "—" : String(value);
    const escapeHtml = value => text(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
    const metric = (metrics, key) => text(metrics && metrics[key]);
    const statusClass = value => `status-${{text(value).toLowerCase().replaceAll(" ", "-").replace(/[^a-z0-9_-]/g, "-")}}`;
    const formatDiagnosis = (diagnosis, fallback = null) => {{
      const lines = [];
      if (diagnosis && diagnosis.reason) {{
        lines.push(text(diagnosis.reason));
      }} else if (fallback) {{
        lines.push(text(fallback));
      }}
      (diagnosis && diagnosis.details ? diagnosis.details : []).forEach(detail => lines.push(`- ${{text(detail)}}`));
      if (diagnosis && diagnosis.time_since_heartbeat_seconds !== undefined && diagnosis.time_since_heartbeat_seconds !== null) {{
        lines.push(`heartbeat_age=${{text(diagnosis.time_since_heartbeat_seconds)}}s`);
      }}
      if (diagnosis && diagnosis.missing_artifacts && diagnosis.missing_artifacts.length) {{
        lines.push(`missing=${{diagnosis.missing_artifacts.join(', ')}}`);
      }}
      return lines.join('\\n') || '—';
    }};

    function renderHealth(run) {{
      const heartbeat = run.heartbeat || {{}};
      const diagnosis = run.diagnosis || {{}};
      document.querySelector('#run-health-strip').innerHTML = `
        <div><span class="label">Run Health Strip</span><div class="value ${{statusClass(run.status)}}">${{escapeHtml(run.status)}}</div></div>
        <div><span class="label">Run ID</span><div class="value">${{escapeHtml(run.run_id)}}</div></div>
        <div><span class="label">Active iteration</span><div class="value">${{escapeHtml(run.active_iteration)}}</div></div>
        <div><span class="label">Latest update</span><div class="value">${{escapeHtml(run.latest_update)}}</div></div>
        <div><span class="label">Heartbeat freshness</span><div class="value">${{escapeHtml(heartbeat.age_seconds)}}s</div></div>
        <div><span class="label">Diagnosis</span><div class="value">${{escapeHtml(formatDiagnosis(diagnosis, run.stop_reason)).replaceAll('\\n', '<br>')}}</div></div>
      `;
    }}

    function nodeLabel(iteration) {{
      return iteration.hypothesis || iteration.strategy_change_summary || `Iteration ${{iteration.iteration}}`;
    }}

    function resetSelectedPanel() {{
      const detailLink = document.querySelector('#open-detail-link');
      detailLink.href = '#';
      detailLink.textContent = 'Open detail page';
      document.querySelector('#hypothesis-diff').textContent = 'No iteration selected.';
      document.querySelector('#strategy-diff').textContent = 'No strategy change yet.';
      document.querySelector('#metric-breakdown').textContent = 'No metrics yet.';
      document.querySelector('#decision-reasoning').textContent = 'No decision yet.';
    }}

    function renderTimeline(iterations) {{
      const timeline = document.querySelector('#iteration-timeline');
      if (!iterations.length) {{
        timeline.innerHTML = '<div class="empty">Waiting for iterations…</div>';
        selectedIteration = null;
        resetSelectedPanel();
        return;
      }}
      if (!selectedIteration || !iterations.some(item => item.iteration === selectedIteration)) {{
        selectedIteration = iterations[iterations.length - 1].iteration;
      }}
      timeline.innerHTML = iterations.map(iteration => `
        <button class="node ${{statusClass(iteration.status)}}" aria-selected="${{iteration.iteration === selectedIteration}}" data-iteration="${{escapeHtml(iteration.iteration)}}">
          <div class="node-title"><span>#${{escapeHtml(iteration.iteration)}} · ${{escapeHtml(iteration.status)}}</span><span>${{escapeHtml(iteration.decision)}}</span></div>
          <p>${{escapeHtml(nodeLabel(iteration))}}</p>
          <div class="metric-row">
            <span class="metric">drawdown<strong>${{escapeHtml(metric(iteration.metrics, 'drawdown'))}}</strong></span>
            <span class="metric">turnover<strong>${{escapeHtml(metric(iteration.metrics, 'turnover'))}}</strong></span>
            <span class="metric">deflated_sr<strong>${{escapeHtml(metric(iteration.metrics, 'deflated_sr'))}}</strong></span>
            <span class="metric">baseline delta<strong>${{escapeHtml(metric(iteration.metrics, 'baseline_delta'))}}</strong></span>
          </div>
        </button>
      `).join('');
      timeline.querySelectorAll('.node').forEach(node => {{
        node.addEventListener('click', () => {{
          selectedIteration = Number(node.dataset.iteration);
          renderTimeline(iterations);
          renderSelected(iterations);
        }});
      }});
    }}

    function renderSelected(iterations) {{
      const selected = iterations.find(item => item.iteration === selectedIteration) || iterations[iterations.length - 1];
      if (!selected) return;
      const analysis = selected.analysis || {{}};
      const breakdown = selected.metric_breakdown || {{ current: selected.metrics || {{}}, comparisons: [] }};
      const detailLink = document.querySelector('#open-detail-link');
      detailLink.href = `/iterations/${{selected.iteration}}`;
      detailLink.textContent = `Open iteration ${{selected.iteration}}`;
      document.querySelector('#hypothesis-diff').textContent = text(analysis.hypothesis_diff || selected.hypothesis);
      document.querySelector('#strategy-diff').textContent = text(analysis.strategy_diff || selected.strategy_change_summary);
      document.querySelector('#metric-breakdown').textContent = formatMetricBreakdown(breakdown);
      document.querySelector('#decision-reasoning').textContent = formatDecisionReasoning(selected);
    }}

    function formatMetricBreakdown(breakdown) {{
      const lines = ['Current metrics:', JSON.stringify(breakdown.current || {{}}, null, 2), '', 'Comparisons:'];
      (breakdown.comparisons || []).forEach(comparison => {{
        lines.push(`${{comparison.label}} · ${{text(comparison.summary)}}`);
      }});
      return lines.join('\\n');
    }}

    function formatDecisionReasoning(iteration) {{
      const reasons = iteration.decision_reasons || [];
      const lines = [`Decision: ${{text(iteration.decision)}}`];
      if (reasons.length) {{
        lines.push('Reasons:');
        reasons.forEach(reason => lines.push(`- ${{reason}}`));
      }} else {{
        lines.push('No decision reasons recorded yet.');
      }}
      const diagnosis = formatDiagnosis(iteration.diagnosis);
      if (diagnosis !== '—') {{
        lines.push('', 'Diagnosis:', diagnosis);
      }}
      return lines.join('\\n');
    }}

    function renderSupport(state) {{
      const iterations = state.iterations || [];
      const latest = iterations[iterations.length - 1] || {{}};
      const logs = iterations.flatMap(iteration => iteration.logs || []).slice(-6).reverse();
      document.querySelector('#recent-activity').innerHTML = logs.length
        ? logs.map(log => `<p><strong>${{escapeHtml(log.updated_at)}}</strong><br>${{escapeHtml(text(log.excerpt).slice(0, 180))}}</p>`).join('')
        : 'No logs yet.';
      document.querySelector('#artifact-availability').textContent = latest.artifacts
        ? Object.entries(latest.artifacts).map(([name, exists]) => `${{name}}: ${{exists ? 'yes' : 'no'}}`).join('\\n')
        : 'No artifacts yet.';
      document.querySelector('#performance-trend').textContent = (state.ledger.rows || [])
        .map((row, index) => `#${{index + 1}} score=${{text(row.score)}} deflated_sr=${{text(row.deflated_sr)}} drawdown=${{text(row.drawdown)}}`)
        .slice(-6)
        .join('\\n') || 'No ledger data yet.';
      document.querySelector('#decision-summary').textContent = iterations
        .map(iteration => `#${{iteration.iteration}} ${{text(iteration.decision)}} — ${{(iteration.decision_reasons || []).join(', ') || 'no reason recorded'}}`)
        .slice(-6)
        .join('\\n') || 'No decisions yet.';
    }}

    async function loadDashboardState() {{
      const response = await fetch('/api/state', {{ cache: 'no-store' }});
      const state = await response.json();
      renderHealth(state.run || {{}});
      renderTimeline(state.iterations || []);
      renderSelected(state.iterations || []);
      renderSupport(state);
      document.querySelector('#last-refresh').textContent = new Date().toLocaleTimeString();
    }}

    loadDashboardState().catch(error => {{
      document.querySelector('#last-refresh').textContent = `Refresh failed: ${{error.message}}`;
    }});
    setInterval(loadDashboardState, {refresh_milliseconds});
  </script>
</body>
</html>
"""


def render_iteration_detail_index(iteration_number: int, *, refresh_seconds: float = 3.0) -> str:
    """Render a drill-down page for one iteration."""
    refresh_milliseconds = max(1, int(refresh_seconds * 1000))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Iteration {iteration_number} Detail · Quant Autoresearch</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #090c10;
      --panel: rgba(17, 23, 31, 0.86);
      --panel-strong: rgba(25, 35, 46, 0.96);
      --line: rgba(141, 232, 255, 0.22);
      --ink: #e9f7ff;
      --muted: #90a8b5;
      --cyan: #56e4ff;
      --lime: #c6ff5c;
      --amber: #ffcc66;
      --red: #ff6b7a;
      --shadow: 0 22px 80px rgba(0, 0, 0, 0.45);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      min-height: 100vh;
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 18% 12%, rgba(86, 228, 255, 0.18), transparent 30rem),
        radial-gradient(circle at 82% 18%, rgba(198, 255, 92, 0.10), transparent 28rem),
        linear-gradient(135deg, #06080c 0%, #0d1218 54%, #11171f 100%);
      font-family: "Avenir Next", "Gill Sans", "Trebuchet MS", sans-serif;
      letter-spacing: 0.01em;
    }}
    main {{
      width: min(1320px, calc(100vw - 40px));
      margin: 0 auto;
      padding: 32px 0 44px;
    }}
    a {{ color: var(--lime); text-decoration: none; }}
    .masthead {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 24px;
      margin-bottom: 20px;
    }}
    h1 {{
      margin: 0;
      font-family: "Copperplate", "Avenir Next", sans-serif;
      font-size: clamp(2rem, 5vw, 4.6rem);
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    .eyebrow, .label {{
      color: var(--cyan);
      font-size: 0.74rem;
      font-weight: 800;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }}
    .refresh {{
      color: var(--muted);
      text-align: right;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      font-size: 0.74rem;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(5, minmax(120px, 1fr));
      gap: 1px;
      margin-bottom: 18px;
      border: 1px solid var(--line);
      border-radius: 24px;
      overflow: hidden;
      background: var(--line);
      box-shadow: var(--shadow);
    }}
    .summary div {{
      min-height: 94px;
      padding: 16px;
      background: var(--panel-strong);
    }}
    .value {{
      margin-top: 8px;
      font-size: clamp(1.05rem, 2vw, 1.6rem);
      font-weight: 800;
      word-break: break-word;
    }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(380px, 1fr) minmax(320px, 0.75fr);
      gap: 18px;
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 24px;
      background: var(--panel);
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    .panel h2, .panel h3 {{
      margin: 0;
      padding: 18px 20px 12px;
      font-size: 0.82rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--cyan);
      border-bottom: 1px solid var(--line);
    }}
    .detail-section {{
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
    }}
    .detail-section:last-child {{ border-bottom: 0; }}
    pre {{
      white-space: pre-wrap;
      margin: 8px 0 0;
      font-family: "SFMono-Regular", "Menlo", monospace;
      font-size: 0.84rem;
      line-height: 1.5;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 0.88rem;
    }}
    th, td {{
      padding: 10px 8px;
      border-top: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{ color: var(--muted); text-transform: uppercase; letter-spacing: 0.12em; }}
    .muted {{ color: var(--muted); }}
    @media (max-width: 980px) {{
      .grid {{ grid-template-columns: 1fr; }}
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
  </style>
</head>
<body>
  <main>
    <header class="masthead">
      <div>
        <div class="eyebrow"><a href="/">← Back to monitor</a></div>
        <h1>Iteration Detail</h1>
      </div>
      <div class="refresh">Live refresh · <span id="refresh-rate">{refresh_seconds:g}s</span><br><span id="last-refresh">Booting</span></div>
    </header>

    <section class="summary" aria-label="Iteration summary">
      <div><span class="label">Iteration</span><div class="value">#{iteration_number}</div></div>
      <div><span class="label">Status</span><div class="value" id="iteration-detail-status">Loading</div></div>
      <div><span class="label">Decision</span><div class="value" id="iteration-detail-decision">—</div></div>
      <div><span class="label">Score</span><div class="value" id="iteration-detail-score">—</div></div>
      <div><span class="label">Baseline delta</span><div class="value" id="iteration-detail-baseline-delta">—</div></div>
    </section>

    <section class="grid">
      <section class="panel">
        <h2>Approved Reading Order</h2>
        <div class="detail-section"><span class="label">Hypothesis diff</span><pre id="hypothesis-diff">Loading…</pre></div>
        <div class="detail-section"><span class="label">Strategy diff</span><pre id="strategy-diff">Loading…</pre></div>
        <div class="detail-section"><span class="label">Metric breakdown</span><pre id="metric-breakdown">vs previous iteration · vs current baseline · vs best iteration in current run</pre></div>
        <div class="detail-section"><span class="label">Decision reasoning</span><pre id="decision-reasoning">Loading…</pre></div>
      </section>

      <aside>
        <section class="panel">
          <h3>Artifact References</h3>
          <div class="detail-section" id="artifact-references">Loading artifacts…</div>
        </section>
        <section class="panel" style="margin-top:18px">
          <h3>Log Excerpts</h3>
          <div class="detail-section" id="log-excerpts">Loading logs…</div>
        </section>
      </aside>
    </section>
  </main>
  <script>
    const iterationNumber = {iteration_number};
    const text = value => value === null || value === undefined || value === "" ? "—" : String(value);
    const escapeHtml = value => text(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
    const formatDiagnosis = (diagnosis, fallback = null) => {{
      const lines = [];
      if (diagnosis && diagnosis.reason) {{
        lines.push(text(diagnosis.reason));
      }} else if (fallback) {{
        lines.push(text(fallback));
      }}
      (diagnosis && diagnosis.details ? diagnosis.details : []).forEach(detail => lines.push(`- ${{text(detail)}}`));
      if (diagnosis && diagnosis.time_since_heartbeat_seconds !== undefined && diagnosis.time_since_heartbeat_seconds !== null) {{
        lines.push(`heartbeat_age=${{text(diagnosis.time_since_heartbeat_seconds)}}s`);
      }}
      if (diagnosis && diagnosis.missing_artifacts && diagnosis.missing_artifacts.length) {{
        lines.push(`missing=${{diagnosis.missing_artifacts.join(', ')}}`);
      }}
      return lines.join('\\n') || '—';
    }};
    const formatDeltas = deltas => Object.entries(deltas || {{}})
      .map(([key, value]) => `${{key}}: ${{Number(value).toLocaleString(undefined, {{ maximumSignificantDigits: 6, signDisplay: 'always' }})}}`)
      .join(', ') || 'No comparable metrics.';

    function formatMetricBreakdown(breakdown) {{
      const lines = ['Current metrics:', JSON.stringify((breakdown && breakdown.current) || {{}}, null, 2), '', 'Comparisons:'];
      ((breakdown && breakdown.comparisons) || []).forEach(comparison => {{
        lines.push(`${{comparison.label}}`);
        lines.push(`  reference: ${{text(comparison.reference_iteration || comparison.reference_metric)}}`);
        lines.push(`  deltas: ${{formatDeltas(comparison.deltas)}}`);
        lines.push(`  summary: ${{text(comparison.summary)}}`);
      }});
      return lines.join('\\n');
    }}

    function formatDecisionReasoning(iteration) {{
      const reasons = iteration.decision_reasons || [];
      const lines = [`Decision: ${{text(iteration.decision)}}`];
      if (reasons.length) {{
        lines.push('Reasons:');
        reasons.forEach(reason => lines.push(`- ${{reason}}`));
      }} else {{
        lines.push('No decision reasons recorded yet.');
      }}
      const diagnosis = formatDiagnosis(iteration.diagnosis);
      if (diagnosis !== '—') {{
        lines.push('', 'Diagnosis:', diagnosis);
      }}
      return lines.join('\\n');
    }}

    function renderArtifacts(references) {{
      if (!references || !references.length) return 'No artifact references yet.';
      return `<table><thead><tr><th>Name</th><th>Status</th><th>Path</th></tr></thead><tbody>${{references.map(item => `
        <tr><td>${{escapeHtml(item.name)}}</td><td>${{item.exists ? 'present' : 'missing'}}</td><td class="muted">${{escapeHtml(item.path)}}</td></tr>
      `).join('')}}</tbody></table>`;
    }}

    function renderLogs(logs) {{
      if (!logs || !logs.length) return 'No logs yet.';
      return logs.map(log => `<p><strong>${{escapeHtml(log.updated_at)}}</strong><br><span class="muted">${{escapeHtml(log.path)}}</span></p><pre>${{escapeHtml(log.excerpt)}}</pre>`).join('');
    }}

    function resetMissingIterationDetail() {{
      document.querySelector('#iteration-detail-status').textContent = 'Missing';
      document.querySelector('#iteration-detail-decision').textContent = '—';
      document.querySelector('#iteration-detail-score').textContent = '—';
      document.querySelector('#iteration-detail-baseline-delta').textContent = '—';
      document.querySelector('#hypothesis-diff').textContent = 'No iteration selected.';
      document.querySelector('#strategy-diff').textContent = 'No strategy change yet.';
      document.querySelector('#metric-breakdown').textContent = 'No metrics yet.';
      document.querySelector('#decision-reasoning').textContent = 'No decision yet.';
      document.querySelector('#artifact-references').innerHTML = 'No artifact references yet.';
      document.querySelector('#log-excerpts').innerHTML = 'No logs yet.';
    }}

    function renderIterationDetail(state) {{
      const selected = (state.iterations || []).find(item => item.iteration === iterationNumber);
      if (!selected) {{
        resetMissingIterationDetail();
        document.querySelector('#last-refresh').textContent = new Date().toLocaleTimeString();
        return;
      }}
      const analysis = selected.analysis || {{}};
      const breakdown = selected.metric_breakdown || {{ current: selected.metrics || {{}}, comparisons: [] }};
      document.querySelector('#iteration-detail-status').textContent = text(selected.status);
      document.querySelector('#iteration-detail-decision').textContent = text(selected.decision);
      document.querySelector('#iteration-detail-score').textContent = text(selected.metrics && selected.metrics.score);
      document.querySelector('#iteration-detail-baseline-delta').textContent = text(selected.metrics && selected.metrics.baseline_delta);
      document.querySelector('#hypothesis-diff').textContent = text(analysis.hypothesis_diff || selected.hypothesis);
      document.querySelector('#strategy-diff').textContent = text(analysis.strategy_diff || selected.strategy_change_summary);
      document.querySelector('#metric-breakdown').textContent = formatMetricBreakdown(breakdown);
      document.querySelector('#decision-reasoning').textContent = formatDecisionReasoning(selected);
      document.querySelector('#artifact-references').innerHTML = renderArtifacts(selected.artifact_references || []);
      document.querySelector('#log-excerpts').innerHTML = renderLogs(selected.logs || []);
      document.querySelector('#last-refresh').textContent = new Date().toLocaleTimeString();
    }}

    async function loadIterationDetail() {{
      const response = await fetch('/api/state', {{ cache: 'no-store' }});
      renderIterationDetail(await response.json());
    }}

    loadIterationDetail().catch(error => {{
      document.querySelector('#last-refresh').textContent = `Refresh failed: ${{error.message}}`;
    }});
    setInterval(loadIterationDetail, {refresh_milliseconds});
  </script>
</body>
</html>
"""


def _iteration_number_from_path(path: str) -> int | None:
    prefix = "/iterations/"
    if not path.startswith(prefix):
        return None
    value = path.removeprefix(prefix).strip("/")
    if not value.isdigit():
        return None
    return int(value)


def make_dashboard_handler(repo_root: str | Path, *, refresh_seconds: float = 3.0) -> type[BaseHTTPRequestHandler]:
    """Build a request handler bound to a repo root."""
    resolved_root = Path(repo_root)

    class DashboardRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path in {"/", "/index.html"}:
                self._send_text(
                    render_dashboard_index(refresh_seconds=refresh_seconds),
                    content_type="text/html; charset=utf-8",
                )
                return
            iteration_number = _iteration_number_from_path(path)
            if iteration_number is not None:
                self._send_text(
                    render_iteration_detail_index(iteration_number, refresh_seconds=refresh_seconds),
                    content_type="text/html; charset=utf-8",
                )
                return
            if path == "/api/state":
                self._send_json(observe_dashboard_state(resolved_root))
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Dashboard resource not found")

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_text(self, payload: str, *, content_type: str) -> None:
            encoded = payload.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(self, payload: dict[str, Any]) -> None:
            self._send_text(
                json.dumps(payload, ensure_ascii=False),
                content_type="application/json; charset=utf-8",
            )

    return DashboardRequestHandler


def serve_dashboard(
    *,
    repo_root: str | Path,
    host: str = "127.0.0.1",
    port: int = 8765,
    refresh_seconds: float = 3.0,
) -> None:
    """Serve the read-only dashboard until interrupted."""
    handler = make_dashboard_handler(repo_root, refresh_seconds=refresh_seconds)
    server = ThreadingHTTPServer((host, port), handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()

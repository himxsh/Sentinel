const DEMO_SIGNAL = {
  title: "Runaway analytical query exhausting connection pool",
  severity: "P1",
  cluster_ref: "kooky-efreet",
  details: {
    metric: "connection_pool_usage",
    value: 0.95,
    unit: "percent",
    query: "SELECT COUNT(*) FROM large_table CROSS JOIN another_table",
  },
};

const HOT_RANGE_SIGNAL = {
  title: "Hot range imbalance on orders primary key",
  severity: "P1",
  cluster_ref: "kooky-efreet",
  details: {
    metric: "qps_imbalance",
    value: 10,
    unit: "times",
    table: "orders",
  },
};

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

function toast(msg) {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove("show"), 2800);
}

function shortId(id) {
  return id ? String(id).slice(0, 8) : "";
}

function fmtTs(ts) {
  if (!ts) return "";
  return String(ts).replace("T", " ").slice(0, 19);
}

async function api(path, opts) {
  const r = await fetch(path, opts);
  const text = await r.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  if (!r.ok) {
    const err = new Error((data && data.error) || r.statusText || "request failed");
    err.status = r.status;
    err.data = data;
    throw err;
  }
  return data;
}

async function fireAlert(btn, signal, idleLabel) {
  const label = idleLabel || "Fire demo alert";
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Firing…";
  }
  try {
    const data = await api("/api/alerts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(signal || DEMO_SIGNAL),
    });
    toast("Alert ingested — opening incident");
    if (data.incident_id) {
      window.location.href = `/incidents/${data.incident_id}`;
      return data;
    }
    window.location.href = "/incidents";
    return data;
  } catch (e) {
    toast(`Fire failed: ${e.message}`);
    throw e;
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = label;
    }
  }
}

function fireDemoAlert(btn) {
  return fireAlert(btn, DEMO_SIGNAL, "Fire demo alert");
}

function fireHotRangeAlert(btn) {
  return fireAlert(btn, HOT_RANGE_SIGNAL, "Fire hot-range alert");
}

function pendingGate(events) {
  if (!events || !events.length) return null;
  const approved = new Set();
  const details = [];
  events.forEach((event) => {
    if (event.kind !== "approval" || !event.detail || typeof event.detail !== "object") return;
    details.push(event.detail);
    const body = event.detail.approved;
    if (body && typeof body === "object") approved.add(body.cmd || "*");
    else if (body) approved.add("*");
  });
  if (approved.has("*")) return null;
  for (const detail of details) {
    const awaiting = detail.awaiting;
    if (!awaiting || typeof awaiting !== "object") continue;
    if (awaiting.cmd && approved.has(awaiting.cmd)) continue;
    return { action: awaiting, reason: detail.reason || "", impact: detail.impact || null };
  }
  return null;
}

function pendingApproval(events) {
  const gate = pendingGate(events);
  return gate ? gate.action : null;
}

function storyFrom(events) {
  let hits = [];
  const impacts = [];
  const seen = new Set();
  let runbook = null;
  (events || []).forEach((event) => {
    const detail = event.detail || {};
    if (!hits.length && Array.isArray(detail.recalled) && detail.recalled.length) {
      hits = detail.recalled.filter((row) => row && row.why);
    }
    const impact = detail.impact || (detail.dry_run && detail.dry_run.impact);
    if (impact && impact.cmd && !seen.has(impact.cmd)) {
      seen.add(impact.cmd);
      impacts.push(impact);
    }
    if (typeof detail.title === "string" && Array.isArray(detail.steps)) runbook = detail;
  });
  return { hits, impacts, runbook };
}

function fillPanel(panelId, bodyId, html) {
  const panel = document.getElementById(panelId);
  const body = document.getElementById(bodyId);
  if (!panel || !body) return;
  if (!html) {
    panel.hidden = true;
    body.innerHTML = "";
    return;
  }
  panel.hidden = false;
  body.innerHTML = html;
}

function renderStory(incident) {
  const { hits, impacts, runbook } = storyFrom(incident.events);
  fillPanel(
    "recallPanel",
    "recallBody",
    hits
      .map(
        (hit) => `<article class="event">
          <div class="event-head"><span class="event-kind">${esc(hit.band || "match")}</span><span>${esc(hit.source || "")}</span></div>
          <p><strong>${esc(hit.title || "Untitled")}</strong></p>
          <p>${esc(hit.why)}</p>
        </article>`
      )
      .join("")
  );
  fillPanel(
    "impactPanel",
    "impactBody",
    impacts
      .map((impact) => {
        const usd = typeof impact.estimated_usd === "number" ? `$${impact.estimated_usd}/month` : "n/a";
        const verdict = impact.hold ? impact.why_hold || "Waits for approval." : "Clear to apply.";
        return `<article class="event">
          <div class="event-head"><span class="event-kind">${esc(impact.cmd)}</span><span>${esc(impact.scope || "")}</span><span>${esc(usd)}</span><span>${esc(impact.risk || "")} risk</span></div>
          <p>${esc(impact.targets || "")}</p>
          <p class="muted">${esc(verdict)}</p>
        </article>`;
      })
      .join("")
  );
  if (!runbook) {
    fillPanel("runbookPanel", "runbookBody", "");
    return;
  }
  const steps = (runbook.steps || [])
    .map((step) => {
      const mark = step.status === "applied" ? "Applied" : "Held";
      return `<li><strong>${esc(mark)}.</strong> ${esc(step.do || step.cmd || "")}</li>`;
    })
    .join("");
  const checks = (runbook.checks || []).map(esc).join(" ");
  const undo = (runbook.rollback || []).map(esc).join(" ");
  fillPanel(
    "runbookPanel",
    "runbookBody",
    `<p><strong>${esc(runbook.title)}</strong></p><ol>${steps}</ol>` +
      (checks ? `<p class="muted">Check: ${checks}</p>` : "") +
      (undo ? `<p class="muted">Undo: ${undo}</p>` : "")
  );
}

function renderEvents(container, events) {
  if (!events || !events.length) {
    container.innerHTML = '<p class="empty">No audit events yet.</p>';
    return;
  }
  container.innerHTML = events
    .map(
      (e) => `<article class="event">
      <div class="event-head">
        <span class="event-kind">${esc(e.kind)}</span>
        <span>${esc(e.actor)}</span>
        <span>${esc(fmtTs(e.ts))}</span>
      </div>
      <pre>${esc(JSON.stringify(e.detail, null, 2))}</pre>
    </article>`
    )
    .join("");
}

window.SentinelUI = {
  DEMO_SIGNAL,
  HOT_RANGE_SIGNAL,
  esc,
  toast,
  shortId,
  fmtTs,
  api,
  fireDemoAlert,
  fireHotRangeAlert,
  pendingApproval,
  pendingGate,
  renderEvents,
  renderStory,
};

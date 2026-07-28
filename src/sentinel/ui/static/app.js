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

async function fireDemoAlert(btn) {
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Firing…";
  }
  try {
    const data = await api("/api/alerts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(DEMO_SIGNAL),
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
      btn.textContent = "Fire demo alert";
    }
  }
}

function pendingApproval(events) {
  if (!events || !events.length) return null;
  for (let i = events.length - 1; i >= 0; i--) {
    const e = events[i];
    if (e.kind === "approval" && e.detail && e.detail.awaiting && !e.detail.approved) {
      return e.detail.awaiting;
    }
  }
  return null;
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
  esc,
  toast,
  shortId,
  fmtTs,
  api,
  fireDemoAlert,
  pendingApproval,
  renderEvents,
};

"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  ACTIVE_STATUSES,
  asRecord,
  fmtTs,
  kindLabel,
  pendingApproval,
  shortId,
  statusLabel,
} from "@/lib/format";
import type { Incident, IncidentEvent } from "@/lib/types";
import { toast } from "@/components/ToastHost";

function EventBody({ event }: { event: IncidentEvent }) {
  const detail = asRecord(event.detail);
  const recalled = Array.isArray(detail?.recalled_titles)
    ? detail.recalled_titles.filter((title): title is string => typeof title === "string")
    : [];
  const hypothesis = typeof detail?.hypothesis === "string" ? detail.hypothesis : null;
  const awaiting = Boolean(detail?.awaiting && !detail.approved);
  const approved = Boolean(detail?.approved);

  let summary: string | null = null;
  if (recalled.length) {
    summary = `Remembered ${recalled.length} similar case${recalled.length === 1 ? "" : "s"}.`;
  } else if (hypothesis) {
    summary = hypothesis;
  } else if (awaiting) {
    summary = "A change needs your OK before it runs.";
  } else if (approved) {
    summary = "Approved and recorded.";
  } else if (typeof detail?.summary === "string") {
    summary = detail.summary;
  }

  return (
    <>
      {summary ? <p className="m-0">{summary}</p> : null}
      <details>
        <summary className="cursor-pointer font-mono text-[0.75rem] text-ink-muted">Raw note</summary>
        <pre>{JSON.stringify(event.detail, null, 2)}</pre>
      </details>
    </>
  );
}

export function IncidentDetail({ id }: { id: string }) {
  const [incident, setIncident] = useState<Incident | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);

  const refresh = useCallback(async () => {
    const next = await api<Incident>(`/api/incidents/${id}`);
    setIncident(next);
    return ACTIVE_STATUSES.has(next.status);
  }, [id]);

  useEffect(() => {
    let timer: number | null = null;
    let source: EventSource | null = null;

    refresh()
      .then((live) => {
        if (typeof EventSource !== "undefined") {
          source = new EventSource(`/api/incidents/${id}/stream`);
          source.onmessage = () => {
            refresh().catch(() => {});
            source?.close();
          };
          source.onerror = () => source?.close();
        }
        if (live) {
          timer = window.setInterval(() => {
            refresh()
              .then((stillLive) => {
                if (!stillLive && timer) {
                  window.clearInterval(timer);
                  timer = null;
                }
              })
              .catch(() => {});
          }, 2000);
        }
      })
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : "Case not found.");
      });

    return () => {
      if (timer) window.clearInterval(timer);
      source?.close();
    };
  }, [id, refresh]);

  async function approve() {
    setApproving(true);
    try {
      const data = await api<{ approved?: boolean }>(`/api/incidents/${id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      toast(data.approved ? "Approved. The action is recorded." : "Approve failed.");
      await refresh();
    } catch (caught) {
      toast(caught instanceof Error ? caught.message : "Approve failed.");
    } finally {
      setApproving(false);
    }
  }

  if (error) {
    return (
      <p className="text-ink-muted" role="alert">
        {error}
      </p>
    );
  }

  if (!incident) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        <div className="skeleton h-40" />
        <div className="skeleton h-40" />
        <div className="skeleton h-64 md:col-span-2" />
      </div>
    );
  }

  const live = ACTIVE_STATUSES.has(incident.status);
  const awaiting = pendingApproval(incident.events);

  return (
    <>
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="m-0 max-w-[28ch] text-[2.15rem] leading-[1.15] tracking-[-0.02em]">
            {incident.title}
          </h1>
          <p className="meta mt-3">
            <span className={`badge sev-${incident.severity}`}>{incident.severity}</span>
            <span className={`status-${incident.status}`}>{statusLabel(incident.status)}</span>
            <span>{shortId(incident.id)}</span>
            <span>{fmtTs(incident.created_at)}</span>
          </p>
        </div>
        <p className="meta m-0">
          <span className={live ? "live-dot on" : "live-dot"} aria-hidden="true" />
          <span>{live ? "Still working" : "Settled"}</span>
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="panel">
          <h2>Case</h2>
          <p>
            <strong>Status.</strong> {statusLabel(incident.status)}
          </p>
          <p>
            <strong>Severity.</strong> {incident.severity}
          </p>
          <p className="font-mono text-sm text-ink-muted">Updated {fmtTs(incident.updated_at)}</p>
          {awaiting ? (
            <div className="mt-4">
              <button type="button" className="btn btn-ink" disabled={approving} onClick={approve}>
                {approving ? "Recording…" : "Approve this change"}
              </button>
              <p className="mt-2 font-mono text-sm text-ink-muted">
                {JSON.stringify(awaiting)}
              </p>
            </div>
          ) : null}
        </section>

        <section className="panel">
          <h2>What it concluded</h2>
          {incident.hypothesis ? (
            <p>
              <strong>Guess.</strong> {incident.hypothesis}
            </p>
          ) : (
            <p className="text-ink-muted">Waiting for a hypothesis…</p>
          )}
          {incident.resolution ? (
            <p className="mt-3">
              <strong>Write-up.</strong> {incident.resolution}
            </p>
          ) : (
            <p className="mt-3 text-ink-muted">The postmortem lands here when the case closes.</p>
          )}
        </section>

        <section className="panel md:col-span-2">
          <h2>Audit timeline</h2>
          {incident.events?.length ? (
            incident.events.map((event, index) => (
              <article className="event" key={event.id ?? `${event.ts}-${index}`}>
                <div className="event-head">
                  <span className="event-kind">{kindLabel(event.kind)}</span>
                  <span>{event.actor}</span>
                  <span>{fmtTs(event.ts)}</span>
                </div>
                <EventBody event={event} />
              </article>
            ))
          ) : (
            <p className="text-ink-muted">No audit events yet.</p>
          )}
        </section>
      </div>
    </>
  );
}

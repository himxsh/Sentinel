"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  ACTIVE_STATUSES,
  asRecord,
  filedRunbook,
  fmtTs,
  impactPreviews,
  kindLabel,
  pendingGate,
  recallHits,
  shortId,
  statusLabel,
  type ImpactView,
} from "@/lib/format";
import type { Incident, IncidentEvent, ReplayBeat } from "@/lib/types";
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
    summary = typeof detail?.reason === "string" ? detail.reason : "A change needs your OK before it runs.";
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
        <pre data-lenis-prevent>{JSON.stringify(event.detail, null, 2)}</pre>
      </details>
    </>
  );
}

function dollars(value: number | null): string {
  return value === null ? "n/a" : `$${value}`;
}

function ImpactFacts({ impact }: { impact: ImpactView }) {
  return (
    <article className="event">
      <div className="event-head">
        <span className="event-kind">{impact.cmd}</span>
        <span>{impact.scope}</span>
        <span>{dollars(impact.estimated_usd)}/month</span>
        <span className={`risk-${impact.risk}`}>{impact.risk} risk</span>
        <span>{impact.hold ? "Waits" : "Auto"}</span>
      </div>
      <p className="m-0">{impact.targets}</p>
      <p className="mt-2 mb-0 text-ink-muted">{impact.hold ? impact.why_hold : "Clear to apply."}</p>
    </article>
  );
}

export function IncidentDetail({ id }: { id: string }) {
  const [incident, setIncident] = useState<Incident | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);
  const [replayIndex, setReplayIndex] = useState(0);
  const [playing, setPlaying] = useState(false);

  const refresh = useCallback(async () => {
    const next = await api<Incident>(`/api/incidents/${id}`);
    setIncident(next);
    return ACTIVE_STATUSES.has(next.status);
  }, [id]);

  useEffect(() => {
    let timer: number | null = null;
    let source: EventSource | null = null;
    let cancelled = false;

    api<Incident>(`/api/incidents/${id}`)
      .then((next) => {
        if (cancelled) return;
        setIncident(next);
        const live = ACTIVE_STATUSES.has(next.status);
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
        if (cancelled) return;
        setError(caught instanceof Error ? caught.message : "Case not found.");
      });

    return () => {
      cancelled = true;
      if (timer) window.clearInterval(timer);
      source?.close();
    };
  }, [id, refresh]);

  const beats: ReplayBeat[] = incident?.replay ?? [];
  const beatCount = beats.length;
  const safeIndex = beatCount === 0 ? 0 : Math.min(replayIndex, beatCount - 1);

  useEffect(() => {
    if (!playing || beatCount === 0) return;
    const timer = window.setInterval(() => {
      setReplayIndex((current) => (current + 1) % beatCount);
    }, 1600);
    return () => window.clearInterval(timer);
  }, [playing, beatCount]);

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
  const gate = pendingGate(incident.events);
  const hits = recallHits(incident.events);
  const impacts = impactPreviews(incident.events);
  const runbook = filedRunbook(incident.events);
  const beat = beatCount ? beats[safeIndex] : undefined;
  const approveCmd = typeof gate?.action.cmd === "string" ? gate.action.cmd : "this change";
  const gateImpact = impacts.find((item) => item.cmd === approveCmd) ?? null;

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
          {gate ? (
            <div className="mt-4">
              <p className="m-0">{gate.reason || "A change needs your OK before it runs."}</p>
              {gateImpact ? (
                <p className="mt-2 font-mono text-sm text-ink-muted">
                  {gateImpact.scope} blast · {dollars(gateImpact.estimated_usd)}/month · {gateImpact.risk} risk
                </p>
              ) : null}
              <button type="button" className="btn btn-ink mt-3" disabled={approving} onClick={approve}>
                {approving ? "Recording…" : `Approve ${approveCmd}`}
              </button>
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

        {hits.length ? (
          <section className="panel md:col-span-2" id="why-recalled">
            <h2>Why these cases</h2>
            <div className="grid gap-3">
              {hits.map((hit) => (
                <article key={hit.title} className="event">
                  <div className="event-head">
                    <span className="event-kind">{hit.band}</span>
                    <span>{hit.source}</span>
                  </div>
                  <p className="m-0">
                    <strong>{hit.title}</strong>
                  </p>
                  <p className="mt-2 mb-0">{hit.why}</p>
                </article>
              ))}
            </div>
          </section>
        ) : null}

        {impacts.length ? (
          <section className="panel md:col-span-2" id="blast-radius">
            <h2>Blast radius</h2>
            <p className="mt-0 text-ink-muted">Priced before anything runs. The numbers are a rate card, not an invoice.</p>
            <div className="grid gap-3">
              {impacts.map((impact) => (
                <ImpactFacts key={impact.cmd} impact={impact} />
              ))}
            </div>
          </section>
        ) : null}

        {runbook ? (
          <section className="panel md:col-span-2" id="runbook-filed">
            <h2>Runbook</h2>
            <p className="mt-0">
              <strong>{runbook.title}</strong>
            </p>
            <ol className="m-0 grid list-decimal gap-2 pl-5">
              {runbook.steps.map((step) => (
                <li key={`${step.status}-${step.cmd}`}>
                  <span className={step.status === "applied" ? "step-applied" : "step-held"}>
                    {step.status === "applied" ? "Applied. " : "Held. "}
                  </span>
                  {step.do}
                </li>
              ))}
            </ol>
            {runbook.checks.length ? (
              <p className="text-ink-muted">Check: {runbook.checks.join(" ")}</p>
            ) : null}
            {runbook.rollback.length ? <p className="text-ink-muted">Undo: {runbook.rollback.join(" ")}</p> : null}
            {runbook.markdown ? (
              <details className="mt-2">
                <summary className="cursor-pointer font-mono text-[0.75rem] text-ink-muted">Markdown</summary>
                <pre data-lenis-prevent>{runbook.markdown}</pre>
              </details>
            ) : null}
          </section>
        ) : null}

        {beat ? (
          <section className="panel md:col-span-2" id="replay" aria-label="Replay the night">
            <h2>Replay the night</h2>
            <p id="replay-narration" className="beat" aria-live="polite">
              {beat.narration}
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  setPlaying(false);
                  setReplayIndex((current) => (current - 1 + beatCount) % beatCount);
                }}
              >
                Back
              </button>
              <button
                type="button"
                id="replay-play"
                className="btn btn-ink"
                aria-pressed={playing}
                onClick={() => setPlaying((current) => !current)}
              >
                {playing ? "Pause" : "Play"}
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  setPlaying(false);
                  setReplayIndex((current) => (current + 1) % beatCount);
                }}
              >
                Next
              </button>
              <span className="meta">
                {safeIndex + 1} / {beatCount} · {beat.label}
              </span>
            </div>
          </section>
        ) : null}

        <section className="panel md:col-span-2">
          <h2>Audit timeline</h2>
          {incident.events?.length ? (
            incident.events.map((event, index) => (
              <article
                className={beat && index === safeIndex ? "event is-current" : "event"}
                key={event.id ?? `${event.ts}-${index}`}
              >
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

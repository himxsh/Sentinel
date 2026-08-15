import { FireAlertButton } from "@/components/FireAlertButton";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { fmtTs, shortId, statusLabel } from "@/lib/format";
import type { IncidentSummary } from "@/lib/types";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function IncidentsPage() {
  let incidents: IncidentSummary[] = [];
  let error: string | null = null;

  try {
    incidents = await api<IncidentSummary[]>("/api/incidents");
  } catch (caught) {
    error = caught instanceof Error ? caught.message : "Could not load cases.";
  }

  return (
    <div className="shell shell-narrow">
      <Header current="incidents" />
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="m-0 text-[1.875rem] font-semibold tracking-[-0.02em]">Cases</h1>
          <p className="mt-2 max-w-[42ch] text-ink-muted">
            Live memory of every alert Sentinel has opened, looked into, and filed.
          </p>
        </div>
        <FireAlertButton />
      </div>

      {error ? (
        <p className="text-ink-muted" role="alert">
          {error}
        </p>
      ) : incidents.length === 0 ? (
        <p className="text-ink-muted">No cases yet. Fire a demo alert to open the first one.</p>
      ) : (
        <ul className="feed">
          {incidents.map((incident) => (
            <li key={incident.id}>
              <Link href={`/incidents/${incident.id}`}>
                <span className="feed-title">{incident.title}</span>
                <span className="meta">
                  <span className={`badge sev-${incident.severity}`}>{incident.severity}</span>
                  <span className={`status-${incident.status}`}>{statusLabel(incident.status)}</span>
                  <span>{shortId(incident.id)}</span>
                  <span>{fmtTs(incident.created_at)}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

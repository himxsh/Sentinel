import type { IncidentEvent } from "./types";

export const DEMO_SIGNAL = {
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

export const STATUS_LABEL: Record<string, string> = {
  open: "Opened",
  diagnosing: "Looking",
  remediating: "Fixing",
  resolved: "Resolved",
  failed: "Failed",
};

export const KIND_LABEL: Record<string, string> = {
  observation: "Noted",
  decision: "Decided",
  approval: "Approval",
  action: "Acted",
};

export const ACTIVE_STATUSES = new Set(["open", "diagnosing", "remediating"]);

export function statusLabel(status: string): string {
  return STATUS_LABEL[status] ?? status;
}

export function kindLabel(kind: string): string {
  return KIND_LABEL[kind] ?? kind;
}

export function shortId(id: string): string {
  return id.slice(0, 8);
}

export function fmtTs(ts: string | null): string {
  if (!ts) return "";
  return ts.replace("T", " ").slice(0, 19);
}

export function pendingApproval(events: IncidentEvent[] | undefined): Record<string, unknown> | null {
  if (!events?.length) return null;
  for (let i = events.length - 1; i >= 0; i--) {
    const event = events[i];
    if (event.kind !== "approval") continue;
    const detail = asRecord(event.detail);
    if (detail?.awaiting && !detail.approved) {
      return asRecord(detail.awaiting) ?? { awaiting: detail.awaiting };
    }
    return null;
  }
  return null;
}

export function asRecord(value: unknown): Record<string, unknown> | null {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

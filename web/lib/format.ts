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

export const HOT_RANGE_SIGNAL = {
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

export type PendingGate = {
  action: Record<string, unknown>;
  impact: Record<string, unknown> | null;
  reason: string;
};

export type RecallHit = {
  title: string;
  source: string;
  band: string;
  why: string;
};

export type ImpactView = {
  cmd: string;
  scope: string;
  targets: string;
  estimated_ru: number | null;
  estimated_usd: number | null;
  risk: string;
  hold: boolean;
  why_hold: string;
};

export type RunbookStep = { cmd: string; status: string; do: string };

export type RunbookView = {
  title: string;
  steps: RunbookStep[];
  checks: string[];
  rollback: string[];
  markdown: string;
};

// Keep in step with pending_action in src/sentinel/impact.py.
export function pendingGate(events: IncidentEvent[] | undefined): PendingGate | null {
  if (!events?.length) return null;
  const approved = new Set<string>();
  const details: Record<string, unknown>[] = [];
  for (const event of events) {
    if (event.kind !== "approval") continue;
    const detail = asRecord(event.detail);
    if (!detail) continue;
    details.push(detail);
    const body = detail.approved;
    const approvedRecord = asRecord(body);
    if (approvedRecord) {
      const cmd = approvedRecord.cmd;
      approved.add(typeof cmd === "string" && cmd ? cmd : "*");
    } else if (body) {
      approved.add("*");
    }
  }
  if (approved.has("*")) return null;
  for (const detail of details) {
    const awaiting = asRecord(detail.awaiting);
    if (!awaiting) continue;
    const cmd = awaiting.cmd;
    if (typeof cmd === "string" && approved.has(cmd)) continue;
    return {
      action: awaiting,
      impact: asRecord(detail.impact),
      reason: typeof detail.reason === "string" ? detail.reason : "",
    };
  }
  return null;
}

export function pendingApproval(events: IncidentEvent[] | undefined): Record<string, unknown> | null {
  return pendingGate(events)?.action ?? null;
}

export function recallHits(events: IncidentEvent[] | undefined): RecallHit[] {
  for (const event of events ?? []) {
    const recalled = asRecord(event.detail)?.recalled;
    if (!Array.isArray(recalled) || !recalled.length) continue;
    return recalled.flatMap((item) => {
      const row = asRecord(item);
      if (!row || typeof row.why !== "string") return [];
      return [
        {
          title: typeof row.title === "string" ? row.title : "Untitled",
          source: typeof row.source === "string" ? row.source : "memory",
          band: typeof row.band === "string" ? row.band : "unknown",
          why: row.why,
        },
      ];
    });
  }
  return [];
}

export function impactPreviews(events: IncidentEvent[] | undefined): ImpactView[] {
  const byCmd = new Map<string, ImpactView>();
  for (const event of events ?? []) {
    const detail = asRecord(event.detail);
    const raw = asRecord(detail?.impact) ?? asRecord(asRecord(detail?.dry_run)?.impact);
    if (!raw || typeof raw.cmd !== "string") continue;
    byCmd.set(raw.cmd, {
      cmd: raw.cmd,
      scope: typeof raw.scope === "string" ? raw.scope : "unknown",
      targets: typeof raw.targets === "string" ? raw.targets : "",
      estimated_ru: typeof raw.estimated_ru === "number" ? raw.estimated_ru : null,
      estimated_usd: typeof raw.estimated_usd === "number" ? raw.estimated_usd : null,
      risk: typeof raw.risk === "string" ? raw.risk : "unknown",
      hold: Boolean(raw.hold),
      why_hold: typeof raw.why_hold === "string" ? raw.why_hold : "",
    });
  }
  return [...byCmd.values()];
}

export function filedRunbook(events: IncidentEvent[] | undefined): RunbookView | null {
  let found: RunbookView | null = null;
  for (const event of events ?? []) {
    const detail = asRecord(event.detail);
    if (!detail || typeof detail.title !== "string" || !Array.isArray(detail.steps)) continue;
    const steps = detail.steps.flatMap((item) => {
      const step = asRecord(item);
      if (!step || typeof step.do !== "string") return [];
      return [
        {
          cmd: typeof step.cmd === "string" ? step.cmd : "unknown",
          status: typeof step.status === "string" ? step.status : "held",
          do: step.do,
        },
      ];
    });
    found = {
      title: detail.title,
      steps,
      checks: stringList(detail.checks),
      rollback: stringList(detail.rollback),
      markdown: typeof detail.markdown === "string" ? detail.markdown : "",
    };
  }
  return found;
}

function stringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string");
}

export function asRecord(value: unknown): Record<string, unknown> | null {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

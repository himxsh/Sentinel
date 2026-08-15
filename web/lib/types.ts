export type IncidentSummary = {
  id: string;
  title: string;
  severity: string;
  status: string;
  created_at: string | null;
};

export type IncidentEvent = {
  id?: string;
  actor: string;
  kind: string;
  detail: unknown;
  ts: string | null;
};

export type Incident = IncidentSummary & {
  hypothesis: string | null;
  resolution: string | null;
  updated_at: string | null;
  events: IncidentEvent[];
};

export type AlertResult = {
  incident_id?: string;
  status?: string;
  hypothesis?: string;
};

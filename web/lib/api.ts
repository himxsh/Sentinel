const BACKEND = process.env.SENTINEL_API_URL ?? "http://127.0.0.1:8000";

export function apiUrl(path: string): string {
  if (typeof window === "undefined") {
    return `${BACKEND}${path}`;
  }
  return path;
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), { cache: "no-store", ...init });
  } catch {
    throw new Error("Could not reach the agent. Start it with uvicorn, then try again.");
  }

  const text = await response.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }

  if (!response.ok) {
    const record = data && typeof data === "object" ? (data as { error?: string }) : null;
    throw new Error(record?.error || response.statusText || "Request failed");
  }

  return data as T;
}

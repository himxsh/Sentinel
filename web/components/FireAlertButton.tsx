"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { DEMO_SIGNAL } from "@/lib/format";
import type { AlertResult } from "@/lib/types";
import { toast } from "@/components/ToastHost";

export function FireAlertButton({
  signal = DEMO_SIGNAL,
  label = "Fire a demo alert",
  className = "btn btn-signal",
  id,
}: {
  signal?: Record<string, unknown>;
  label?: string;
  className?: string;
  id?: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function onClick() {
    setBusy(true);
    try {
      const data = await api<AlertResult>("/api/alerts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(signal),
      });
      toast("Case opened. Opening it now.");
      router.push(data.incident_id ? `/incidents/${data.incident_id}` : "/incidents");
    } catch (error) {
      toast(error instanceof Error ? error.message : "Could not fire the alert.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <button type="button" id={id} className={className} disabled={busy} onClick={onClick}>
      {busy ? "Working through the case…" : label}
    </button>
  );
}

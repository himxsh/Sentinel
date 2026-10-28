import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { filedRunbook, impactPreviews, pendingApproval, pendingGate, recallHits, shortId, statusLabel } from "../lib/format.ts";

assert.ok(createRequire(import.meta.url).resolve("lenis/react"));

assert.equal(shortId("abcdefghijklmnop"), "abcdefgh");
assert.equal(statusLabel("diagnosing"), "Looking");
assert.equal(statusLabel("mystery"), "mystery");

assert.equal(pendingApproval([]), null);
assert.deepEqual(
  pendingApproval([
    { actor: "agent", kind: "approval", detail: { awaiting: { op: "kill" } }, ts: "1" },
    { actor: "user", kind: "approval", detail: { approved: true }, ts: "2" },
  ]),
  null,
);
assert.deepEqual(
  pendingApproval([
    { actor: "agent", kind: "approval", detail: { awaiting: { op: "kill" } }, ts: "1" },
  ]),
  { op: "kill" },
);
assert.equal(
  pendingGate([
    { actor: "agent", kind: "approval", detail: { awaiting: { cmd: "scatter_range" }, reason: "wide" }, ts: "1" },
    { actor: "agent", kind: "approval", detail: { awaiting: { cmd: "enable_random_uuids" }, reason: "keys" }, ts: "2" },
    { actor: "user", kind: "approval", detail: { approved: { cmd: "enable_random_uuids" } }, ts: "3" },
  ])?.action.cmd,
  "scatter_range",
);

const story = [
  {
    actor: "agent",
    kind: "observation",
    detail: { recalled: [{ title: "Hot range", source: "runbook", band: "near", why: "Shares range." }] },
    ts: "1",
  },
  {
    actor: "agent",
    kind: "observation",
    detail: { impact: { cmd: "scatter_range", scope: "cluster", targets: "ranges", estimated_ru: 250000, estimated_usd: 42, risk: "high", hold: true, why_hold: "cluster-wide" } },
    ts: "2",
  },
  {
    actor: "agent",
    kind: "observation",
    detail: {
      title: "Runbook: Hot range",
      steps: [{ cmd: "scatter_range", status: "held", do: "Scatter it." }],
      checks: ["Watch QPS."],
      rollback: ["Leave it."],
      markdown: "# Runbook",
    },
    ts: "3",
  },
];
assert.equal(recallHits(story)[0].why, "Shares range.");
assert.equal(impactPreviews(story)[0].estimated_usd, 42);
assert.equal(filedRunbook(story)?.steps[0].status, "held");

console.log("web/lib/format.ts ok");

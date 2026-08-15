import assert from "node:assert/strict";
import { pendingApproval, shortId, statusLabel } from "../lib/format.ts";

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

console.log("web/lib/format.ts ok");

import test from "node:test";
import assert from "node:assert/strict";
import {
  validateDraft,
  portableDraft,
  activationSteps,
} from "../api/changes.mjs";

const change = {
  table: "spawn2",
  key: { id: 42 },
  before: { id: 42, zone: "ecommons", version: 0, x: 1 },
  after: { id: 42, zone: "ecommons", version: 0, x: 2 },
};
const draft = {
  format: 1,
  id: "459e7f8b-3144-4976-bb5b-18aad387af04",
  title: "Move guard",
  revision: 1,
  source: "local",
  changes: [change],
  receipts: [],
};
test("portable change sets do not contain local deployment metadata", () => {
  const exported = portableDraft({
    ...draft,
    receipts: [{ privateBackupPath: "secret-path" }],
    published: { localDirectory: "private" },
  });
  assert.equal(exported.receipts, undefined);
  assert.equal(exported.published, undefined);
  assert.equal(exported.changes[0].before.x, 1);
});
test("import validation rejects protected columns, duplicates and arbitrary tables", () => {
  assert.doesNotThrow(() => validateDraft(draft));
  assert.throws(
    () => validateDraft({ ...draft, changes: [change, change] }),
    /duplicate/i,
  );
  assert.throws(() =>
    validateDraft({ ...draft, changes: [{ ...change, table: "accounts" }] }),
  );
  assert.throws(
    () =>
      validateDraft({
        ...draft,
        changes: [
          { ...change, after: { ...change.after, zone: "poknowledge" } },
        ],
      }),
    /cannot be edited/i,
  );
  assert.throws(() =>
    validateDraft({ ...draft, changes: [{ ...change, after: { x: 2 } }] }),
  );
});
test("activation distinguishes NPC cache from spawn repop and loot regeneration", () => {
  assert.match(activationSteps([change]).join(" "), /saved state/i);
  assert.match(activationSteps([{ table: "npc_types" }]).join(" "), /restart/i);
  assert.match(
    activationSteps([{ table: "lootdrop_entries" }]).join(" "),
    /shared_memory/i,
  );
});

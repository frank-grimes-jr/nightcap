import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { DraftStore } from "../api/store.mjs";

test("drafts survive restart and stale saves do not overwrite newer edits", async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), "npc-drafts-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const store = new DraftStore(root);
  const draft = await store.create("Move tunnel residents", "local");
  await store.save({ ...draft, title: "Move residents near bank" }, 1);
  const restarted = new DraftStore(root);
  const found = await restarted.get(draft.id);
  assert.equal(found.title, "Move residents near bank");
  assert.equal(found.revision, 2);
  await assert.rejects(
    store.save({ ...draft, title: "Stale title" }, 1),
    /changed/i,
  );
  assert.equal((await store.list()).length, 1);
});
test("draft IDs cannot escape the storage folder", async () => {
  const store = new DraftStore(os.tmpdir());
  await assert.rejects(store.get("../config.local"), /invalid/i);
});

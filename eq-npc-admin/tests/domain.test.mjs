import test from "node:test";
import assert from "node:assert/strict";
import {
  makeChange,
  reverseChange,
  equalRows,
  sqlPreview,
  validatePatch,
  parseLocation,
} from "../api/domain.mjs";

const spawn = {
  id: 42,
  zone: "ecommons",
  version: 0,
  spawngroupID: 7,
  x: 10,
  y: 20,
  z: 3,
  heading: 0,
  respawntime: 640,
};
test("placement changes preserve the original snapshot and reverse exactly", () => {
  const change = makeChange("spawn2", { id: 42 }, spawn, {
    x: -1506,
    y: -185,
    heading: 256,
  });
  assert.equal(spawn.x, 10);
  assert.equal(change.after.x, -1506);
  assert.deepEqual(reverseChange(change).after, spawn);
  assert.deepEqual(reverseChange(reverseChange(change)), change);
});
test("compares database numeric strings without ignoring other drift", () => {
  assert.equal(equalRows({ id: 42, x: 1.25 }, { x: "1.25", id: "42" }), true);
  assert.equal(
    equalRows({ id: 42, name: "001" }, { id: 42, name: "1" }),
    false,
  );
  assert.equal(equalRows({ id: 42, x: 1 }, { id: 42, x: 2 }), false);
  assert.equal(
    equalRows({ hp: "9007199254740993" }, { hp: 9007199254740992 }),
    false,
  );
});
test("refuses forbidden tables, columns, primary-key changes and invalid numbers", () => {
  assert.throws(
    () => validatePatch("rule_values", { rule_value: 1 }),
    /table/i,
  );
  for (const patch of [
    { id: 3 },
    { x: "" },
    { x: null },
    { x: Infinity },
    { heading: 512 },
    { respawntime: -1 },
    { x: "1; DROP TABLE spawn2" },
  ]) {
    assert.throws(() => makeChange("spawn2", { id: 42 }, spawn, patch));
  }
  assert.throws(() =>
    validatePatch("npc_types", JSON.parse('{"__proto__":1}')),
  );
  assert.throws(() => validatePatch("lootdrop_entries", { chance: 101 }));
});
test("rejects edits that make no change", () => {
  assert.throws(
    () => makeChange("spawn2", { id: 42 }, spawn, { x: 10 }),
    /no change/i,
  );
});
test("loot item insertion and removal preserve composite keys", () => {
  const key = { lootdrop_id: 9, item_id: 5015 };
  const added = makeChange(
    "lootdrop_entries",
    key,
    null,
    { chance: 12.5, item_charges: 1 },
    "insert",
  );
  assert.deepEqual(added.key, key);
  assert.equal(added.after.item_id, 5015);
  assert.equal(reverseChange(added).after, null);
});
test("SQL review uses full before-image guards and escapes text without SQL modes", () => {
  const change = makeChange(
    "npc_types",
    { id: 2 },
    { id: 2, name: "Guard", level: 10 },
    { name: "Guard'; DROP TABLE items; --" },
  );
  const sql = sqlPreview([change]);
  assert.match(sql, /<=>/);
  assert.match(sql, /`level`/);
  assert.ok(!sql.includes("Guard'; DROP"));
  assert.match(sql, /review only/i);
});
test("parses EverQuest loc order y,x,z without swapping axes", () => {
  assert.deepEqual(parseLocation("Your Location is -185.00, -1506.25, 2.00"), {
    x: -1506.25,
    y: -185,
    z: 2,
  });
  assert.throws(() => parseLocation("some arbitrary words 1 2 3"));
});
test("curated class-hub stock cannot bypass the repository catalog workflow", () => {
  assert.throws(
    () =>
      makeChange(
        "merchantlist",
        { merchantid: 99300, slot: 1 },
        { merchantid: 99300, slot: 1, item: 17708 },
        { item: 5015 },
      ),
    /catalog/i,
  );
  assert.throws(
    () =>
      makeChange(
        "npc_types",
        { id: 997900 },
        { id: 997900, merchant_id: 99300, class: 41 },
        { merchant_id: 22 },
      ),
    /catalog/i,
  );
  assert.doesNotThrow(() =>
    makeChange(
      "merchantlist",
      { merchantid: 100, slot: 1 },
      { merchantid: 100, slot: 1, item: 5015 },
      { item: 5016 },
    ),
  );
});

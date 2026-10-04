import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, writeFile, rm, mkdir } from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { MapStore, parseMap } from "../api/maps.mjs";
import {
  worldToMap,
  fitView,
  project,
  zoomView,
  clipHeight,
  spawnPairs,
} from "../src/map.js";

test("client maps align with known PoK bankers; view preserves aspect ratio and cursor zoom", () => {
  assert.deepEqual(
    worldToMap({ x: 484, y: 447, z: -124.125 }),
    [-484, -447, -124.125],
  );
  const view = fitView(
    [
      [-500, -500],
      [500, 500],
    ],
    800,
    400,
  );
  const a = project([-100, 0], view, 800, 400),
    b = project([0, -100], view, 800, 400),
    c = project([0, 0], view, 800, 400);
  assert.equal(c[0] - a[0], c[1] - b[1]);
  const next = zoomView(view, 2, 100, 120, 800, 400);
  const world = [
    view.x + (100 - 400) / view.scale,
    view.y + (120 - 200) / view.scale,
  ];
  assert.deepEqual(project(world, next, 800, 400), [100, 120]);
  assert.ok(Number.isFinite(fitView([], 300, 400).scale));
});
test("height slice clips stairs crossing a floor and rejects other floors", () => {
  assert.deepEqual(
    clipHeight([0, 0, -50, 100, 200, 50, 1], -10, 10),
    [40, 80, -10, 60, 120, 10, 1],
  );
  assert.equal(clipHeight([0, 0, 50, 100, 200, 50, 0], -10, 10), null);
  assert.deepEqual(
    clipHeight([0, 0, 0, 100, 200, 0, 0], -10, 10),
    [0, 0, 0, 100, 200, 0, 0],
  );
});
test("staged markers retain before/after and isolate zone versions", () => {
  const spawns = [
    { id: 1, zone: "poknowledge", version: 0, x: 484, y: 447, z: -124 },
    { id: 2, zone: "poknowledge", version: 1, x: 9, y: 9, z: 9 },
  ];
  const after = { ...spawns[0], x: 500, z: -110 };
  const pairs = spawnPairs(
    spawns,
    [{ table: "spawn2", key: { id: "1" }, after }],
    "poknowledge:0",
  );
  assert.equal(pairs.length, 1);
  assert.deepEqual(pairs[0].after, after);
  assert.equal(pairs[0].before.x, 484);
});
test("map parser accepts lines, labels and layers but rejects nonfinite and malformed data", () => {
  const m = parseMap(
    "L 1,2,3,4,5,6,0,0,0\nP 4,5,6,0,0,0,2,The_Bank\nL NaN,2,3,4,5,6,0,0,0\nP 1,2,3\n",
    2,
  );
  assert.deepEqual(m.lines, [[1, 2, 3, 4, 5, 6, 2]]);
  assert.equal(m.labels[0].text, "The Bank");
  assert.equal(m.labels[0].layer, 2);
  assert.equal(m.invalid, 2);
});
test("map reader handles layers, version aliases, missing maps, cache refresh and traversal", async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), "npc-maps-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const line = "L 1,2,3,4,5,6,0,0,0\n";
  await writeFile(path.join(root, "poknowledge.txt"), line);
  await writeFile(path.join(root, "poknowledge_1.txt"), line);
  const maps = new MapStore(root);
  const m = await maps.get("poknowledge", 0);
  assert.equal(m.available, true);
  assert.equal(m.lines.length, 2);
  assert.deepEqual(m.files, ["poknowledge.txt", "poknowledge_1.txt"]);
  assert.ok(!JSON.stringify(m).includes(root));
  await writeFile(path.join(root, "poknowledge.txt"), line + line);
  assert.equal((await maps.get("poknowledge", 0)).lines.length, 3);
  assert.equal(
    (await maps.get("other", 2, { "other:2": "poknowledge" })).lines.length,
    3,
  );
  assert.equal((await maps.get("missing", 0)).available, false);
  assert.equal((await new MapStore().get("poknowledge", 0)).available, false);
  for (const name of ["../private", "..%2fprivate", "C:\\private", "bad.txt"])
    await assert.rejects(maps.get(name, 0));
  await assert.rejects(
    maps.get("poknowledge", 0, { "poknowledge:0": "../private" }),
  );
  await assert.rejects(maps.get("poknowledge", NaN));
  await mkdir(path.join(root, "dir.txt"));
  await assert.rejects(maps.get("dir", 0));
  await writeFile(
    path.join(root, "huge.txt"),
    Buffer.alloc(8 * 1024 * 1024 + 1),
  );
  await assert.rejects(maps.get("huge", 0), /8 MB/);
});

import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { mkdtemp, rm, readFile, readdir } from "node:fs/promises";
import { createApp } from "../api/app.mjs";
import { atomicJson } from "../api/store.mjs";
import path from "node:path";
import os from "node:os";
import {
  createPool,
  rows,
  readRecord,
  insertDefaults,
} from "../api/database.mjs";
import { makeChange } from "../api/domain.mjs";
import { assess, deploy, rollbackDraft } from "../api/changes.mjs";

// Deliberately fixed test-only port/database. Never points at the normal PEQ target.
const pool = createPool({
  database: {
    host: "127.0.0.1",
    port: 3317,
    user: "root",
    password: "npc-admin-test-only",
    database: "npc_admin_test",
  },
});
const schema = [
  "CREATE TABLE npc_types (id INT PRIMARY KEY, name VARCHAR(64), level INT DEFAULT 10, hp BIGINT DEFAULT 100 CHECK(hp <= 2000), loottable_id INT DEFAULT 8, merchant_id INT DEFAULT 0) ENGINE=InnoDB",
  "CREATE TABLE zone (zoneidnumber INT, short_name VARCHAR(32), long_name VARCHAR(64), version INT, PRIMARY KEY(zoneidnumber,version)) ENGINE=InnoDB",
  "CREATE TABLE spawn2 (id INT PRIMARY KEY, zone VARCHAR(32), version INT, spawngroupID INT, x FLOAT, y FLOAT, z FLOAT, heading FLOAT, respawntime INT DEFAULT 640) ENGINE=InnoDB",
  "CREATE TABLE spawnentry (spawngroupID INT, npcID INT, chance INT) ENGINE=InnoDB",
  "CREATE TABLE loottable (id INT PRIMARY KEY, name VARCHAR(64), mincash INT DEFAULT 0, maxcash INT DEFAULT 0) ENGINE=InnoDB",
  "CREATE TABLE loottable_entries (loottable_id INT, lootdrop_id INT, probability FLOAT DEFAULT 100, multiplier INT DEFAULT 1, droplimit INT DEFAULT 0, mindrop INT DEFAULT 0) ENGINE=InnoDB",
  "CREATE TABLE lootdrop (id INT PRIMARY KEY, name VARCHAR(64)) ENGINE=InnoDB",
  "CREATE TABLE lootdrop_entries (lootdrop_id INT, item_id INT, chance FLOAT DEFAULT 1, item_charges INT DEFAULT 1, equip_item INT DEFAULT 0, multiplier INT DEFAULT 1, content_flags VARCHAR(255) DEFAULT NULL) ENGINE=InnoDB",
  "CREATE TABLE items (id INT PRIMARY KEY, Name VARCHAR(64)) ENGINE=InnoDB",
  "CREATE TABLE global_loot (id INT PRIMARY KEY, loottable_id INT, description VARCHAR(64), enabled INT) ENGINE=InnoDB",
  "CREATE TABLE merchantlist (merchantid INT, slot INT, item INT, level_required INT DEFAULT 0, probability FLOAT DEFAULT 100, min_status INT DEFAULT 0, max_status INT DEFAULT 255, bucket_name VARCHAR(100) DEFAULT '', bucket_value VARCHAR(100) DEFAULT '', bucket_comparison INT DEFAULT 0) ENGINE=InnoDB",
  "CREATE TABLE zone_state_spawns (id BIGINT PRIMARY KEY, zone_id INT, instance_id INT, is_corpse INT, is_zone INT, npc_id INT, spawn2_id INT, x FLOAT, y FLOAT, z FLOAT, heading FLOAT, loot_data TEXT) ENGINE=InnoDB",
];
async function reset() {
  const [{ name }] = await rows(pool, "SELECT DATABASE() AS name");
  assert.equal(name, "npc_admin_test");
  for (const table of [
    "npc_admin_deployments",
    ...schema.map((s) => s.split(" ")[2]),
  ])
    await pool.query(`DROP TABLE IF EXISTS ${table}`);
  for (const statement of schema) await pool.query(statement);
  for (const statement of [
    "INSERT INTO npc_types (id,name) VALUES (1,'Guard_A'),(2,'Guard_B')",
    "INSERT INTO zone VALUES (22,'ecommons','East Commonlands',0),(22,'ecommons','Alternate',1),(151,'bazaar','Bazaar',0)",
    "INSERT INTO spawn2 VALUES (42,'ecommons',0,7,10,20,3,0,640),(43,'ecommons',0,9,15,22,4,0,640)",
    "INSERT INTO spawnentry VALUES (7,1,100),(9,2,100)",
    "INSERT INTO loottable VALUES (8,'Shared guard loot',0,20)",
    "INSERT INTO loottable_entries (loottable_id,lootdrop_id) VALUES (8,9)",
    "INSERT INTO lootdrop VALUES (9,'Weapons')",
    "INSERT INTO lootdrop_entries (lootdrop_id,item_id,chance) VALUES (9,5015,10)",
    "INSERT INTO items VALUES (5015,'Rusty Scythe'),(5016,'Rusty Sword')",
    "INSERT INTO global_loot VALUES (1,8,'Global test reward',1)",
    "INSERT INTO zone_state_spawns VALUES (1,22,0,0,0,1,42,10,20,3,0,'saved loot'),(2,22,0,1,0,1,42,10,20,3,0,'corpse'),(3,22,0,0,0,2,43,15,22,4,0,'unrelated'),(4,151,0,0,0,1,42,10,20,3,0,'wrong zone')",
  ])
    await pool.query(statement);
}
const draft = (changes) => ({
  format: 1,
  id: randomUUID(),
  revision: 1,
  source: "test",
  title: "Integration rehearsal",
  changes,
});
const move = async () =>
  makeChange(
    "spawn2",
    { id: 42 },
    await readRecord(pool, "spawn2", { id: 42 }),
    { x: -1506.25, y: -185, heading: 256 },
  );

test("disposable MariaDB deployment and rollback contract", async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), "npc-db-"));
  t.after(async () => {
    await pool.end();
    await rm(root, { recursive: true, force: true });
  });
  const apply = async (d, plan, extra = {}) =>
    deploy({
      pool,
      draft: d,
      targetId: "test",
      previewHash: plan.hash,
      maintenanceConfirmed: true,
      backupRoot: root,
      ...extra,
    });
  await t.test(
    "placement apply and rollback retain corpse, unrelated and wrong-zone state",
    async () => {
      await reset();
      const d = draft([await move()]);
      const plan = await assess(pool, d, "test");
      assert.equal(plan.ready, true);
      assert.deepEqual(
        plan.states.map((s) => Number(s.id)),
        [1],
      );
      const beforeStates = await rows(
        pool,
        "SELECT * FROM zone_state_spawns ORDER BY id",
      );
      const receipt = await apply(d, plan);
      assert.equal((await readRecord(pool, "spawn2", { id: 42 })).x, -1506.25);
      assert.deepEqual(
        (await rows(pool, "SELECT id FROM zone_state_spawns ORDER BY id")).map(
          (s) => Number(s.id),
        ),
        [2, 3, 4],
      );
      assert.equal(
        JSON.parse(
          await readFile(path.join(root, `${receipt.id}.json`), "utf8"),
        ).status,
        "applied",
      );
      await assert.rejects(apply(d, plan), /already has a deployment/);
      const reverse = rollbackDraft(receipt),
        rollbackPlan = await assess(pool, reverse, "test");
      await apply(reverse, rollbackPlan, {
        direction: "rollback",
        priorReceipt: receipt,
      });
      assert.equal((await readRecord(pool, "spawn2", { id: 42 })).x, 10);
      assert.deepEqual(
        await rows(pool, "SELECT * FROM zone_state_spawns ORDER BY id"),
        beforeStates,
      );
    },
  );
  await t.test(
    "stale preview cannot overwrite intervening changes",
    async () => {
      await reset();
      const d = draft([await move()]),
        plan = await assess(pool, d, "test");
      await pool.query("UPDATE spawn2 SET x=99 WHERE id=42");
      await assert.rejects(apply(d, plan), /conflicts/);
      assert.equal((await readRecord(pool, "spawn2", { id: 42 })).x, 99);
      assert.equal(
        (await rows(pool, "SELECT * FROM zone_state_spawns")).length,
        4,
      );
    },
  );
  await t.test(
    "database failure after the first write rolls back the whole change set",
    async () => {
      await reset();
      const c = makeChange(
        "npc_types",
        { id: 1 },
        await readRecord(pool, "npc_types", { id: 1 }),
        { hp: 3000 },
      );
      const d = draft([await move(), c]),
        plan = await assess(pool, d, "test");
      await assert.rejects(apply(d, plan));
      assert.equal((await readRecord(pool, "spawn2", { id: 42 })).x, 10);
      assert.equal(
        Number((await readRecord(pool, "npc_types", { id: 1 })).hp),
        100,
      );
      assert.equal(
        (await rows(pool, "SELECT * FROM npc_admin_deployments")).length,
        0,
      );
    },
  );
  await t.test(
    "insert defaults, global sharing and rollback of loot additions",
    async () => {
      await reset();
      const c = makeChange(
        "lootdrop_entries",
        { lootdrop_id: 9, item_id: 5016 },
        null,
        { chance: 12.5, item_charges: 1 },
        "insert",
      );
      c.after = await insertDefaults(pool, c.table, c.after);
      const d = draft([c]),
        plan = await assess(pool, d, "test");
      assert.equal(plan.effects[0].total, 2);
      assert.equal(plan.effects[0].globalLoot.length, 1);
      const receipt = await apply(d, plan);
      assert.equal((await readRecord(pool, c.table, c.key)).chance, 12.5);
      const reverse = rollbackDraft(receipt);
      await apply(reverse, await assess(pool, reverse, "test"), {
        direction: "rollback",
        priorReceipt: receipt,
      });
      assert.equal(await readRecord(pool, c.table, c.key), null);
      assert.equal(
        (await readRecord(pool, c.table, { lootdrop_id: 9, item_id: 5015 }))
          .chance,
        10,
      );
    },
  );
  await t.test(
    "nontransactional tables and instance state block application",
    async () => {
      await reset();
      await pool.query("ALTER TABLE spawn2 ENGINE=MyISAM");
      assert.match(
        (await assess(pool, draft([await move()]), "test")).blocked.join(" "),
        /InnoDB/,
      );
      await pool.query("ALTER TABLE spawn2 ENGINE=InnoDB");
      await pool.query(
        "UPDATE zone_state_spawns SET instance_id=77 WHERE id=1",
      );
      assert.match(
        (await assess(pool, draft([await move()]), "test")).blocked.join(" "),
        /instance/i,
      );
    },
  );
  await t.test(
    "all-version spawns still find their correct saved state without duplicate zone joins",
    async () => {
      await reset();
      await pool.query("UPDATE spawn2 SET version=-1 WHERE id=42");
      const plan = await assess(pool, draft([await move()]), "test");
      assert.deepEqual(
        plan.states.map((s) => Number(s.id)),
        [1],
      );
    },
  );
  await t.test("ambiguous composite keys are refused", async () => {
    await reset();
    await pool.query(
      "INSERT INTO lootdrop_entries (lootdrop_id,item_id) VALUES (9,5015)",
    );
    await assert.rejects(
      readRecord(pool, "lootdrop_entries", { lootdrop_id: 9, item_id: 5015 }),
      /duplicate/,
    );
  });
  await t.test(
    "ordinary FLOAT decimals and BIGINT snapshots apply and roll back",
    async () => {
      await reset();
      const d = draft([
        makeChange(
          "spawn2",
          { id: 42 },
          await readRecord(pool, "spawn2", { id: 42 }),
          { x: 10.1 },
        ),
        makeChange(
          "npc_types",
          { id: 1 },
          await readRecord(pool, "npc_types", { id: 1 }),
          { hp: 200 },
        ),
        makeChange(
          "lootdrop_entries",
          { lootdrop_id: 9, item_id: 5015 },
          await readRecord(pool, "lootdrop_entries", {
            lootdrop_id: 9,
            item_id: 5015,
          }),
          { chance: 33.3 },
        ),
      ]);
      const receipt = await apply(d, await assess(pool, d, "test"));
      assert.equal(
        (await readRecord(pool, "spawn2", { id: 42 })).x,
        Math.fround(10.1),
      );
      assert.equal(
        (
          await readRecord(pool, "lootdrop_entries", {
            lootdrop_id: 9,
            item_id: 5015,
          })
        ).chance,
        Math.fround(33.3),
      );
      const reverse = rollbackDraft(receipt);
      await apply(
        reverse,
        await assess(pool, reverse, "test", false, { restore: true }),
        { direction: "rollback", priorReceipt: receipt },
      );
      assert.equal((await readRecord(pool, "npc_types", { id: 1 })).hp, "100");
      assert.equal((await readRecord(pool, "spawn2", { id: 42 })).x, 10);
    },
  );
  await t.test(
    "merchant defaults and protected metadata survive additions and removal rollback",
    async () => {
      await reset();
      let c = makeChange(
        "merchantlist",
        { merchantid: 10, slot: 1 },
        null,
        { item: 5015 },
        "insert",
      );
      c.after = await insertDefaults(pool, c.table, c.after);
      const d = draft([c]);
      await apply(d, await assess(pool, d, "test"));
      await pool.query(
        "UPDATE merchantlist SET bucket_name='quest_gate',bucket_value='earned' WHERE merchantid=10",
      );
      const original = await readRecord(pool, c.table, c.key);
      const malformed = structuredClone(original);
      malformed.bucket_name = 1;
      await assert.rejects(
        assess(
          pool,
          draft([
            { table: c.table, key: c.key, before: malformed, after: null },
          ]),
          "test",
        ),
        /must be a string/,
      );
      const removal = draft([
        makeChange(c.table, c.key, original, {}, "delete"),
      ]);
      const receipt = await apply(removal, await assess(pool, removal, "test"));
      assert.deepEqual(receipt.draft.changes[0].before, original);
      const reverse = rollbackDraft(receipt);
      await apply(
        reverse,
        await assess(pool, reverse, "test", false, { restore: true }),
        { direction: "rollback", priorReceipt: receipt },
      );
      assert.deepEqual(await readRecord(pool, c.table, c.key), original);
      const injected = draft([
        {
          ...c,
          key: { merchantid: 10, slot: 2 },
          after: { ...c.after, slot: 2, bucket_name: "bypass" },
        },
      ]);
      await assert.rejects(assess(pool, injected, "test"), /default/);
    },
  );
  await t.test(
    "nontransactional restored-state and ledger tables are refused before writes",
    async () => {
      await reset();
      const d = draft([await move()]);
      const receipt = await apply(d, await assess(pool, d, "test"));
      await pool.query("ALTER TABLE zone_state_spawns ENGINE=MyISAM");
      const reverse = rollbackDraft(receipt),
        plan = await assess(pool, reverse, "test", false, { restore: true });
      assert.match(plan.blocked.join(" "), /zone_state_spawns.*InnoDB/);
      await assert.rejects(
        apply(reverse, plan, { direction: "rollback", priorReceipt: receipt }),
        /Preflight/,
      );
      assert.equal(
        (await rows(pool, "SELECT id FROM zone_state_spawns WHERE id=1"))
          .length,
        0,
      );
      await pool.query("ALTER TABLE zone_state_spawns ENGINE=InnoDB");
      await pool.query("ALTER TABLE npc_admin_deployments ENGINE=MyISAM");
      const next = draft([
        makeChange(
          "npc_types",
          { id: 1 },
          await readRecord(pool, "npc_types", { id: 1 }),
          { hp: 150 },
        ),
      ]);
      await assert.rejects(
        apply(next, await assess(pool, next, "test")),
        /npc_admin_deployments.*InnoDB/,
      );
      assert.equal((await readRecord(pool, "npc_types", { id: 1 })).hp, "100");
    },
  );
  await t.test(
    "imported BIGINT before-images cannot lose precision",
    async () => {
      await reset();
      await pool.query(
        "ALTER TABLE npc_types ADD COLUMN legacy_counter BIGINT DEFAULT 9007199254740993",
      );
      const before = await readRecord(pool, "npc_types", { id: 1 });
      const good = makeChange("npc_types", { id: 1 }, before, { hp: 150 });
      const bad = structuredClone(good);
      bad.before.legacy_counter = 9007199254740992;
      bad.after.legacy_counter = 9007199254740992;
      await assert.rejects(assess(pool, draft([bad]), "test"), /exact integer/);
      const d = draft([good]);
      const receipt = await apply(d, await assess(pool, d, "test"));
      assert.equal(
        receipt.draft.changes[0].before.legacy_counter,
        "9007199254740993",
      );
    },
  );
  await t.test(
    "lost commit acknowledgement recovers through the HTTP ledger workflow",
    async () => {
      await reset();
      const d = draft([
        makeChange(
          "npc_types",
          { id: 1 },
          await readRecord(pool, "npc_types", { id: 1 }),
          { hp: 150 },
        ),
      ]);
      const uncertainPool = {
        getConnection: async () => {
          const connection = await pool.getConnection();
          return new Proxy(connection, {
            get(target, key) {
              if (key === "commit")
                return async () => {
                  await target.commit();
                  throw new Error("Injected lost acknowledgement");
                };
              const value = target[key];
              return typeof value === "function" ? value.bind(target) : value;
            },
          });
        },
      };
      await assert.rejects(
        apply(d, await assess(pool, d, "test"), { pool: uncertainPool }),
        /needs recovery/,
      );
      const files = await readdir(root);
      let receipt;
      for (const file of files.filter((f) => f.endsWith(".json"))) {
        const value = JSON.parse(await readFile(path.join(root, file), "utf8"));
        if (value.draftId === d.id) receipt = value;
      }
      assert.equal(receipt.status, "uncertain");
      assert.equal((await readRecord(pool, "npc_types", { id: 1 })).hp, "150");
      await atomicJson(
        path.join(root, "receipts", `${receipt.id}.json`),
        receipt,
      );
      const fixture = createApp(
        {
          targets: [
            {
              id: "test",
              label: "Test",
              database: {
                host: "127.0.0.1",
                port: 3317,
                user: "root",
                password: "npc-admin-test-only",
                database: "npc_admin_test",
              },
            },
          ],
        },
        root,
      );
      const server = fixture.app.listen(0, "127.0.0.1");
      await new Promise((resolve) => server.once("listening", resolve));
      try {
        const response = await fetch(
          `http://127.0.0.1:${server.address().port}/api/receipts/${receipt.id}/recover`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-NPC-Admin": "1" },
            body: "{}",
          },
        );
        assert.equal(response.status, 200);
        assert.equal((await response.json()).status, "applied");
      } finally {
        await new Promise((resolve) => server.close(resolve));
        await fixture.close();
      }
    },
  );
});

import { createHash, randomUUID } from "node:crypto";
import path from "node:path";
import {
  assert,
  tableSpec,
  validKey,
  makeChange,
  changedFields,
  changeIdentity,
  equalRows,
  identifier,
  reverseChange,
} from "./domain.mjs";
import {
  rows,
  readRecord,
  impact,
  savedStates,
  keyWhere,
  insertDefaults,
  storedRow,
  requireTransactional,
} from "./database.mjs";
import { atomicJson } from "./store.mjs";

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object")
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((k) => [k, canonical(value[k])]),
    );
  return value;
}
export const digest = (value) =>
  createHash("sha256")
    .update(JSON.stringify(canonical(value)))
    .digest("hex");
export function portableDraft(draft) {
  return {
    format: 1,
    id: draft.id,
    title: draft.title,
    source: draft.source,
    revision: draft.revision,
    changes: draft.changes,
  };
}
export function validateDraft(draft, { restore = false } = {}) {
  assert(
    draft &&
      draft.format === 1 &&
      typeof draft.title === "string" &&
      draft.title.trim().length > 0 &&
      draft.title.length <= 120,
    "Invalid change-set format or title",
  );
  assert(
    Number.isSafeInteger(draft.revision) && draft.revision >= 1,
    "Invalid revision",
  );
  assert(
    Array.isArray(draft.changes) && draft.changes.length <= 200,
    "A change set can contain at most 200 records",
  );
  const seen = new Set();
  for (const change of draft.changes) {
    const spec = tableSpec(change.table);
    validKey(change.table, change.key);
    const identity = changeIdentity(change);
    assert(!seen.has(identity), "Duplicate record in change set");
    seen.add(identity);
    for (const row of [change.before, change.after]) {
      assert(
        row === null || (row && typeof row === "object" && !Array.isArray(row)),
        "Invalid row snapshot",
      );
      if (row)
        for (const [k, v] of Object.entries(row)) {
          identifier(k);
          assert(
            v === null ||
              typeof v === "string" ||
              (typeof v === "number" && Number.isFinite(v)),
            "Invalid snapshot value",
          );
          assert(
            typeof v !== "string" || v.length <= 10000,
            "Snapshot value too long",
          );
        }
      if (row)
        for (const k of spec.keys)
          assert(
            String(row[k]) === String(change.key[k]),
            "Snapshot key changed",
          );
    }
    assert(change.before !== null || change.after !== null, "Empty operation");
    assert(
      change.before !== null || spec.insert,
      "Inserting this record type is not supported",
    );
    assert(
      change.after !== null || spec.remove,
      "Deleting this record type is not supported",
    );
    // Only a server-owned receipt may restore original values/metadata. Those
    // values may be legacy sentinels or BIGINT strings outside new-edit rules.
    if (restore) continue;
    const patch = Object.fromEntries(
      changedFields(change)
        .filter(
          (k) =>
            !spec.keys.includes(k) &&
            (change.before !== null ||
              (Object.hasOwn(spec.fields, k) && change.after[k] !== null)),
        )
        .map((k) => [k, change.after?.[k]]),
    );
    const validated = makeChange(
      change.table,
      change.key,
      change.before,
      patch,
      change.before === null
        ? "insert"
        : change.after === null
          ? "delete"
          : "update",
    );
    if (change.before !== null)
      assert(
        equalRows(validated.after, change.after),
        "Snapshot fields were removed or changed unexpectedly",
      );
  }
  return draft;
}
export function activationSteps(changes) {
  const tables = new Set(changes.map((c) => c.table));
  const steps = [];
  if (tables.has("spawn2"))
    steps.push(
      "Stop the affected zones before apply so saved state cannot overwrite placement. The app removes only reviewed non-corpse saved state for those spawns. Start those zones afterward; use #repop only when saved-state handling is not needed.",
    );
  if (tables.has("npc_types") || tables.has("merchantlist"))
    steps.push(
      "Restart each affected zone to reload NPC templates and merchant stock. #repop alone does not refresh these caches.",
    );
  if ([...tables].some((t) => t.startsWith("loot")))
    steps.push(
      "Regenerate shared memory with ./bin/shared_memory, then restart affected zones. New loot records require this full activation. Inspect drops in game, including global loot and quest rewards.",
    );
  steps.push(
    "Database application does not prove in-game activation or balance. Complete the listed zone/NPC QA before gameplay promotion.",
  );
  return steps;
}

async function checkReferences(db, change) {
  if (!change.after) return;
  const refs = [];
  const a = change.after;
  if (change.table === "npc_types" && a.loottable_id > 0)
    refs.push(["loottable", "id", a.loottable_id]);
  if (change.table === "loottable_entries")
    refs.push(
      ["loottable", "id", a.loottable_id],
      ["lootdrop", "id", a.lootdrop_id],
    );
  if (change.table === "lootdrop_entries")
    refs.push(["lootdrop", "id", a.lootdrop_id], ["items", "id", a.item_id]);
  if (change.table === "merchantlist") refs.push(["items", "id", a.item]);
  for (const [table, key, value] of refs) {
    assert(
      (
        await rows(
          db,
          `SELECT ${identifier(key)} FROM ${identifier(table)} WHERE ${identifier(key)} = ? LIMIT 1`,
          [value],
        )
      ).length,
      `Referenced ${table} record ${value} does not exist`,
      409,
    );
  }
}
export async function assess(
  db,
  draft,
  targetId,
  lock = false,
  { restore = false } = {},
) {
  validateDraft(draft, { restore });
  assert(draft.changes.length > 0, "Stage at least one edit before previewing");
  const conflicts = [],
    effects = [];
  for (const change of draft.changes) {
    const actual = await readRecord(db, change.table, change.key, lock);
    await storedRow(db, change.table, change.after);
    if (
      !equalRows(
        await storedRow(db, change.table, actual),
        await storedRow(db, change.table, change.before),
      )
    )
      conflicts.push({
        table: change.table,
        key: change.key,
        expected: change.before,
        actual,
      });
    if (!restore && change.before === null) {
      const spec = tableSpec(change.table);
      const editable = Object.fromEntries(
        Object.entries(change.after).filter(
          ([k, v]) =>
            spec.keys.includes(k) ||
            (Object.hasOwn(spec.fields, k) && v !== null),
        ),
      );
      const defaults = await insertDefaults(db, change.table, editable);
      assert(
        equalRows(
          await storedRow(db, change.table, defaults),
          await storedRow(db, change.table, change.after),
        ),
        "Inserted metadata must match the target schema defaults",
        409,
      );
    }
    await checkReferences(db, change);
    effects.push({
      identity: changeIdentity(change),
      ...(await impact(db, change)),
    });
  }
  const states = await savedStates(db, draft.changes, lock);
  const touched = [
    ...new Set([
      ...draft.changes.map((c) => c.table),
      ...(draft.changes.some((c) => c.table === "spawn2")
        ? ["zone_state_spawns"]
        : []),
    ]),
  ];
  const engines = await rows(
    db,
    `SELECT TABLE_NAME AS name, ENGINE AS engine FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN (${touched.map(() => "?").join(",")})`,
    touched,
  );
  const blocked = touched
    .filter((t) => !engines.some((e) => e.name === t && e.engine === "InnoDB"))
    .map((t) => `${t} must use InnoDB for atomic apply and rollback`);
  if (states.some((s) => Number(s.instance_id) !== 0))
    blocked.push(
      "Affected spawns have instance-specific saved state. An explicit instance maintenance plan is required.",
    );
  const needsMaintenance =
    draft.changes.some((c) => c.table === "spawn2") || states.length > 0;
  const result = {
    target: targetId,
    revision: draft.revision,
    conflicts,
    effects,
    states,
    blocked,
    needsMaintenance,
    activation: activationSteps(draft.changes),
  };
  return {
    ...result,
    hash: digest({ draft: portableDraft(draft), result }),
    ready: conflicts.length === 0 && blocked.length === 0,
  };
}
export async function mutateRecord(db, change) {
  const { table, before, after, key } = change;
  if (before === null) {
    const keys = Object.keys(after);
    await db.execute(
      `INSERT INTO ${identifier(table)} (${keys.map(identifier).join(",")}) VALUES (${keys.map(() => "?").join(",")})`,
      keys.map((k) => after[k]),
    );
  } else if (after === null) {
    const [result] = await db.execute(
      `DELETE FROM ${identifier(table)} WHERE ${keyWhere(key)}`,
      Object.values(key),
    );
    assert(
      result.affectedRows === 1,
      "Unexpected delete count; transaction rolled back",
      409,
    );
  } else {
    const fields = changedFields(change);
    const [result] = await db.execute(
      `UPDATE ${identifier(table)} SET ${fields.map((k) => `${identifier(k)} = ?`).join(",")} WHERE ${keyWhere(key)}`,
      [...fields.map((k) => after[k]), ...Object.values(key)],
    );
    assert(
      result.affectedRows === 1,
      "Unexpected update count; transaction rolled back",
      409,
    );
  }
  assert(
    equalRows(
      await storedRow(db, table, await readRecord(db, table, key, true)),
      await storedRow(db, table, after),
    ),
    "Database did not retain the proposed values; transaction rolled back",
    409,
  );
}

const ledgerSql = `CREATE TABLE IF NOT EXISTS npc_admin_deployments (
  id CHAR(36) PRIMARY KEY, draft_id CHAR(36) NOT NULL, revision INT NOT NULL,
  direction VARCHAR(10) NOT NULL, payload_hash CHAR(64) NOT NULL,
  applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY draft_operation (draft_id, revision, direction)
) ENGINE=InnoDB`;

export async function deploy({
  pool,
  draft,
  targetId,
  previewHash,
  maintenanceConfirmed,
  backupRoot,
  direction = "apply",
  priorReceipt = null,
}) {
  assert(
    ["apply", "rollback"].includes(direction),
    "Invalid deployment direction",
  );
  if (direction === "rollback")
    assert(
      priorReceipt &&
        priorReceipt.target === targetId &&
        digest(draft) === digest(rollbackDraft(priorReceipt)),
      "Rollback must exactly match the original applied receipt",
    );
  validateDraft(draft, { restore: direction === "rollback" });
  const db = await pool.getConnection();
  const receipt = {
    id: randomUUID(),
    draftId: draft.id,
    revision: draft.revision,
    target: targetId,
    direction,
    status: "prepared",
    startedAt: new Date().toISOString(),
    draft: portableDraft(draft),
  };
  const backupFile = path.join(backupRoot, `${receipt.id}.json`);
  let locked = false,
    started = false,
    committing = false;
  try {
    const [{ acquired }] = await rows(
      db,
      "SELECT GET_LOCK(CONCAT('npc-admin:', DATABASE()), 0) AS acquired",
    );
    assert(
      Number(acquired) === 1,
      "Another NPC Admin deployment is running",
      409,
    );
    locked = true;
    await db.query(ledgerSql);
    await requireTransactional(db, "npc_admin_deployments");
    const previous = await rows(
      db,
      "SELECT id FROM npc_admin_deployments WHERE draft_id = ? AND revision = ? AND direction = ?",
      [draft.id, draft.revision, direction],
    );
    assert(
      previous.length === 0,
      "This revision already has a deployment receipt. Review history instead of applying again.",
      409,
    );
    await db.query("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE");
    await db.beginTransaction();
    started = true;
    const plan = await assess(db, draft, targetId, true, {
      restore: direction === "rollback",
    });
    assert(
      plan.ready,
      "Preflight found conflicts or unsupported tables. Preview again.",
      409,
    );
    assert(
      plan.hash === previewHash,
      "The preview has changed. Review a new preview before applying.",
      409,
    );
    assert(
      !plan.needsMaintenance || maintenanceConfirmed === true,
      "Confirm the affected zones are stopped before applying placement changes",
    );
    receipt.savedStates = plan.states;
    receipt.activation = plan.activation;
    receipt.payloadHash = digest(portableDraft(draft));
    // Rollback evidence comes from locked target rows, never an imported
    // representation of those rows. Retain the original proposal hash separately.
    receipt.draft = { ...portableDraft(draft), changes: [] };
    for (const change of draft.changes)
      receipt.draft.changes.push({
        ...change,
        before: await readRecord(db, change.table, change.key, true),
      });
    if (direction === "rollback") {
      assert(
        priorReceipt &&
          priorReceipt.status === "applied" &&
          priorReceipt.target === targetId,
        "A matching applied receipt is required for rollback",
      );
      // Restore only exact saved rows captured by the original apply; never replace newer state.
      assert(
        plan.states.length === 0,
        "New saved state exists; stop the zone and review it before rollback",
        409,
      );
      for (const state of priorReceipt.savedStates) {
        assert(
          (
            await rows(
              db,
              "SELECT id FROM zone_state_spawns WHERE id = ? FOR UPDATE",
              [state.id],
            )
          ).length === 0,
          "A saved-state ID has been reused; rollback refused",
          409,
        );
      }
      receipt.restoredStates = priorReceipt.savedStates;
    }
    await atomicJson(backupFile, receipt);
    for (const change of draft.changes) await mutateRecord(db, change);
    for (const state of plan.states) {
      const [result] = await db.execute(
        "DELETE FROM zone_state_spawns WHERE id = ? AND is_corpse = 0 AND is_zone = 0 AND instance_id = 0",
        [state.id],
      );
      assert(
        result.affectedRows === 1,
        "Saved state changed during apply; transaction rolled back",
        409,
      );
    }
    for (const state of receipt.restoredStates ?? []) {
      const keys = Object.keys(state);
      await db.execute(
        `INSERT INTO zone_state_spawns (${keys.map(identifier).join(",")}) VALUES (${keys.map(() => "?").join(",")})`,
        keys.map((k) => state[k]),
      );
    }
    await db.execute(
      "INSERT INTO npc_admin_deployments (id, draft_id, revision, direction, payload_hash) VALUES (?, ?, ?, ?, ?)",
      [receipt.id, draft.id, draft.revision, direction, receipt.payloadHash],
    );
    committing = true;
    await db.commit();
    started = false;
    receipt.status = "applied";
    receipt.finishedAt = new Date().toISOString();
    await atomicJson(backupFile, receipt);
    return receipt;
  } catch (error) {
    if (started) await db.rollback().catch(() => {});
    receipt.status = committing ? "uncertain" : "failed";
    receipt.message = committing
      ? "Commit outcome requires receipt recovery; do not retry this deployment."
      : "Transaction did not complete.";
    await atomicJson(backupFile, receipt).catch(() => {});
    if (committing)
      throw new Error(
        `Deployment outcome needs recovery. Receipt ${receipt.id}`,
      );
    throw error;
  } finally {
    if (locked)
      await db
        .query("SELECT RELEASE_LOCK(CONCAT('npc-admin:', DATABASE()))")
        .catch(() => {});
    db.release();
  }
}
export function rollbackDraft(receipt) {
  assert(
    receipt.status === "applied" && receipt.direction === "apply",
    "Select a successfully applied receipt",
  );
  return {
    ...receipt.draft,
    changes: [...receipt.draft.changes].reverse().map(reverseChange),
  };
}

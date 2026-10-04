import mysql from "mysql2/promise";
import { assert, identifier, validKey, tableSpec } from "./domain.mjs";

export const rows = async (db, sql, params = []) =>
  (await db.execute(sql, params))[0];
export function createPool(target) {
  const config = target.database;
  assert(
    config &&
      typeof config.host === "string" &&
      typeof config.database === "string",
    "Target database configuration is missing",
  );
  assert(
    ["127.0.0.1", "localhost", "::1"].includes(config.host) ||
      (config.ssl && config.ssl.rejectUnauthorized !== false),
    "Remote database connections require verified TLS or a local SSH tunnel",
  );
  return mysql.createPool({
    host: config.host,
    port: config.port ?? 3307,
    user: config.user,
    password: config.password,
    database: config.database,
    ssl: config.ssl,
    connectionLimit: 4,
    connectTimeout: 5000,
    supportBigNumbers: true,
    bigNumberStrings: true,
    dateStrings: true,
    multipleStatements: false,
    charset: "utf8mb4",
  });
}
export function keyWhere(key) {
  return Object.keys(key)
    .map((k) => `${identifier(k)} <=> ?`)
    .join(" AND ");
}
export async function readRecord(db, table, key, lock = false) {
  validKey(table, key);
  const found = await rows(
    db,
    `SELECT * FROM ${identifier(table)} WHERE ${keyWhere(key)}${lock ? " FOR UPDATE" : ""}`,
    Object.values(key),
  );
  assert(
    found.length <= 1,
    "This record key matches duplicate rows. Repair the ambiguous data before editing.",
    409,
  );
  return found[0] ?? null;
}
export async function insertDefaults(db, table, record) {
  tableSpec(table);
  const fields = await rows(
    db,
    "SELECT COLUMN_NAME, COLUMN_DEFAULT, IS_NULLABLE, DATA_TYPE, EXTRA FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
    [table],
  );
  const result = {};
  for (const f of fields) {
    const key = f.COLUMN_NAME;
    if (Object.hasOwn(record, key)) {
      result[key] = record[key];
      continue;
    }
    let value = f.COLUMN_DEFAULT;
    if (value === null || value === "NULL") {
      assert(f.IS_NULLABLE === "YES", `No safe default for ${table}.${key}`);
      result[key] = null;
    } else if (/^'.*'$/.test(value))
      result[key] = value.slice(1, -1).replaceAll("''", "'");
    else if (/^-?\d+(?:\.\d+)?$/.test(value)) result[key] = Number(value);
    else throw new Error(`Unsupported schema default for ${table}.${key}`);
  }
  assert(
    Object.keys(record).every((k) => Object.hasOwn(result, k)),
    "Target schema is missing a field",
  );
  return result;
}
// Normalize by the actual column type, never by how a value happens to look.
// FLOAT uses its native precision; BIGINT remains lossless; text remains text.
export async function storedRow(db, table, row) {
  if (row === null) return null;
  tableSpec(table);
  const fields = await rows(
    db,
    "SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?",
    [table],
  );
  const result = { ...row };
  assert(
    Object.keys(result).every((key) =>
      fields.some((f) => f.COLUMN_NAME === key),
    ),
    `Target schema is missing a ${table} snapshot column`,
    409,
  );
  for (const { COLUMN_NAME: key, DATA_TYPE: type } of fields) {
    if (!Object.hasOwn(result, key) || result[key] === null) continue;
    const value = result[key];
    if (
      ["tinyint", "smallint", "mediumint", "int", "bigint", "year"].includes(
        type,
      )
    ) {
      assert(
        (typeof value === "string" && /^-?\d+$/.test(value)) ||
          (typeof value === "number" && Number.isSafeInteger(value)),
        `${table}.${key} must preserve an exact integer`,
        409,
      );
      result[key] = BigInt(value).toString();
    } else if (["float", "double", "real"].includes(type)) {
      assert(
        (typeof value === "number" ||
          (typeof value === "string" && value.trim() !== "")) &&
          Number.isFinite(Number(value)),
        `${table}.${key} must be numeric`,
        409,
      );
      result[key] =
        type === "float" ? Math.fround(Number(value)) : Number(value);
    } else if (["decimal", "numeric"].includes(type)) {
      assert(
        /^-?\d+(\.\d+)?$/.test(String(value)),
        `${table}.${key} must preserve a decimal value`,
        409,
      );
      const normalized = String(value)
        .replace(/^(-?)0+(?=\d)/, "$1")
        .replace(/(\.\d*?)0+$/, "$1")
        .replace(/\.$/, "");
      result[key] = normalized === "-0" ? "0" : normalized;
    } else {
      assert(
        typeof value === "string",
        `${table}.${key} snapshot must be a string`,
        409,
      );
    }
  }
  return result;
}
export async function requireTransactional(db, table) {
  const found = await rows(
    db,
    "SELECT ENGINE AS engine FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?",
    [table],
  );
  assert(
    found.length === 1 && found[0].engine === "InnoDB",
    `${table} must use InnoDB for atomic apply and rollback`,
    409,
  );
}
export async function searchNpcs(db, { q = "", zone = "", offset = 0 } = {}) {
  const params = [`%${q}%`, /^\d+$/.test(q) ? Number(q) : 0];
  let filter = "(n.name LIKE ? OR n.id = ?)";
  if (zone) {
    filter +=
      " AND EXISTS (SELECT 1 FROM spawnentry se JOIN spawn2 s ON s.spawngroupID = se.spawngroupID WHERE se.npcID = n.id AND s.zone = ?)";
    params.push(zone);
  }
  return rows(
    db,
    `SELECT n.id, n.name, n.lastname, n.level, n.class, n.race, n.hp, n.loottable_id, n.merchant_id,
    (SELECT COUNT(*) FROM spawnentry se JOIN spawn2 s ON s.spawngroupID = se.spawngroupID WHERE se.npcID = n.id) AS spawn_count
    FROM npc_types n WHERE ${filter} ORDER BY n.name, n.id LIMIT 101 OFFSET ${offset}`,
    params,
  );
}
export const zones = (db) =>
  rows(
    db,
    "SELECT short_name, MIN(long_name) AS long_name FROM zone GROUP BY short_name ORDER BY long_name",
  );
export const items = (db, q) =>
  rows(
    db,
    "SELECT id, Name AS name, icon, slots, classes, races, nodrop, lore, minstatus FROM items WHERE Name LIKE ? OR id = ? ORDER BY Name, id LIMIT 60",
    [`%${q}%`, /^\d+$/.test(q) ? Number(q) : 0],
  );
export async function npcDetails(db, id) {
  const npc = await readRecord(db, "npc_types", { id });
  assert(npc, "NPC not found", 404);
  const spawns = await rows(
    db,
    `SELECT s.*, se.chance AS spawn_chance FROM spawn2 s JOIN spawnentry se ON se.spawngroupID = s.spawngroupID WHERE se.npcID = ? ORDER BY s.zone, s.version, s.id`,
    [id],
  );
  const alternatives = await rows(
    db,
    `SELECT DISTINCT se.spawngroupID, n.id, n.name, se.chance FROM spawnentry se JOIN npc_types n ON n.id = se.npcID WHERE se.spawngroupID IN (SELECT spawngroupID FROM spawnentry WHERE npcID = ?) ORDER BY se.spawngroupID, n.id`,
    [id],
  );
  const loot = npc.loottable_id
    ? await readRecord(db, "loottable", { id: Number(npc.loottable_id) })
    : null;
  const lootGroups = npc.loottable_id
    ? await rows(
        db,
        "SELECT le.*, ld.name FROM loottable_entries le JOIN lootdrop ld ON ld.id = le.lootdrop_id WHERE le.loottable_id = ? ORDER BY le.lootdrop_id",
        [npc.loottable_id],
      )
    : [];
  const lootItems = npc.loottable_id
    ? await rows(
        db,
        "SELECT de.*, i.Name AS item_name FROM lootdrop_entries de LEFT JOIN items i ON i.id = de.item_id WHERE de.lootdrop_id IN (SELECT lootdrop_id FROM loottable_entries WHERE loottable_id = ?) ORDER BY de.lootdrop_id, de.item_id",
        [npc.loottable_id],
      )
    : [];
  const merchants = npc.merchant_id
    ? await rows(
        db,
        "SELECT m.*, i.Name AS item_name FROM merchantlist m LEFT JOIN items i ON i.id = m.item WHERE m.merchantid = ? ORDER BY m.slot",
        [npc.merchant_id],
      )
    : [];
  return { npc, spawns, alternatives, loot, lootGroups, lootItems, merchants };
}
export async function impact(db, change) {
  const { table, key } = change;
  let sql, params;
  if (table === "npc_types") {
    sql = "n.id = ?";
    params = [key.id];
  } else if (table === "spawn2") {
    sql =
      "n.id IN (SELECT se.npcID FROM spawnentry se JOIN spawn2 s ON s.spawngroupID = se.spawngroupID WHERE s.id = ?)";
    params = [key.id];
  } else if (table === "merchantlist") {
    sql = "n.merchant_id = ?";
    params = [key.merchantid];
  } else if (["loottable", "loottable_entries"].includes(table)) {
    sql = "n.loottable_id = ?";
    params = [key.loottable_id ?? key.id];
  } else {
    sql =
      "n.loottable_id IN (SELECT loottable_id FROM loottable_entries WHERE lootdrop_id = ?)";
    params = [key.lootdrop_id ?? key.id];
  }
  const [{ total }] = await rows(
    db,
    `SELECT COUNT(*) AS total FROM npc_types n WHERE ${sql}`,
    params,
  );
  const npcs = await rows(
    db,
    `SELECT n.id, n.name FROM npc_types n WHERE ${sql} ORDER BY n.id LIMIT 30`,
    params,
  );
  const locations = await rows(
    db,
    `SELECT DISTINCT s.zone, s.version FROM spawn2 s JOIN spawnentry se ON se.spawngroupID = s.spawngroupID JOIN npc_types n ON n.id = se.npcID WHERE ${sql} ORDER BY s.zone, s.version`,
    params,
  );
  let globalLoot = [];
  if (["loottable", "loottable_entries"].includes(table))
    globalLoot = await rows(
      db,
      "SELECT id, description, enabled FROM global_loot WHERE loottable_id = ?",
      params,
    );
  else if (["lootdrop", "lootdrop_entries"].includes(table))
    globalLoot = await rows(
      db,
      "SELECT id, description, enabled FROM global_loot WHERE loottable_id IN (SELECT loottable_id FROM loottable_entries WHERE lootdrop_id = ?)",
      params,
    );
  return { total: Number(total), npcs, locations, globalLoot };
}

export async function savedStates(db, changes, lock = false) {
  const ids = changes.filter((c) => c.table === "spawn2").map((c) => c.key.id);
  if (!ids.length) return [];
  // Include only non-corpse state for the affected spawn and its actual zone.
  // Instance state is reported separately and blocked until an explicit instance workflow exists.
  return rows(
    db,
    `SELECT zs.* FROM zone_state_spawns zs
    WHERE zs.is_corpse = 0 AND zs.is_zone = 0 AND zs.spawn2_id IN (${ids.map(() => "?").join(",")})
    AND EXISTS (SELECT 1 FROM spawn2 s JOIN zone z ON z.short_name = s.zone WHERE s.id = zs.spawn2_id AND z.zoneidnumber = zs.zone_id)
    ORDER BY zs.id${lock ? " FOR UPDATE" : ""}`,
    ids,
  );
}

const integer = (min, max) => ({ type: "number", min, max, integer: true });
const number = (min, max) => ({ type: "number", min, max });
const string = (maxLength) => ({ type: "string", maxLength });
const id = integer(1, 2147483647);
const ref = integer(0, 2147483647);
const byte = integer(0, 255);
const flag = integer(0, 1);
const percent = number(0, 100);
const era = {
  min_expansion: integer(-1, 99),
  max_expansion: integer(-1, 99),
  content_flags: string(255),
  content_flags_disabled: string(255),
};

export const tables = {
  npc_types: {
    keys: ["id"],
    fields: {
      name: string(64),
      lastname: string(32),
      level: integer(1, 255),
      maxlevel: byte,
      race: integer(1, 65535),
      class: integer(1, 255),
      gender: integer(0, 2),
      size: number(0, 255),
      hp: integer(1, 2147483647),
      mana: ref,
      AC: ref,
      mindmg: ref,
      maxdmg: ref,
      attack_count: integer(-1, 127),
      attack_delay: ref,
      hp_regen_rate: ref,
      mana_regen_rate: ref,
      aggroradius: number(0, 100000),
      assistradius: number(0, 100000),
      runspeed: number(0, 20),
      texture: byte,
      helmtexture: byte,
      loottable_id: ref,
      merchant_id: ref,
      npc_faction_id: ref,
      npc_spells_id: ref,
      bodytype: integer(0, 65535),
      armortint_red: byte,
      armortint_green: byte,
      armortint_blue: byte,
      d_melee_texture1: ref,
      d_melee_texture2: ref,
      findable: flag,
      trackable: flag,
    },
  },
  spawn2: {
    keys: ["id"],
    fields: {
      x: number(-1000000, 1000000),
      y: number(-1000000, 1000000),
      z: number(-1000000, 1000000),
      heading: number(0, 511.9999),
      respawntime: integer(0, 2147483647),
      variance: ref,
      pathgrid: ref,
      animation: byte,
    },
  },
  loottable: {
    keys: ["id"],
    fields: {
      name: string(255),
      mincash: ref,
      maxcash: ref,
      avgcoin: ref,
      ...era,
    },
  },
  lootdrop: { keys: ["id"], fields: { name: string(255), ...era } },
  loottable_entries: {
    keys: ["loottable_id", "lootdrop_id"],
    insert: true,
    remove: true,
    fields: {
      probability: percent,
      multiplier: byte,
      droplimit: byte,
      mindrop: byte,
    },
  },
  lootdrop_entries: {
    keys: ["lootdrop_id", "item_id"],
    insert: true,
    remove: true,
    fields: {
      chance: percent,
      disabled_chance: percent,
      item_charges: integer(0, 65535),
      equip_item: flag,
      multiplier: byte,
      trivial_min_level: integer(0, 65535),
      trivial_max_level: integer(0, 65535),
      npc_min_level: integer(0, 65535),
      npc_max_level: integer(0, 65535),
      ...era,
    },
  },
  merchantlist: {
    keys: ["merchantid", "slot"],
    insert: true,
    remove: true,
    fields: {
      item: id,
      faction_required: integer(-2000, 2000),
      level_required: byte,
      alt_currency_cost: ref,
      classes_required: ref,
      probability: percent,
      ...era,
    },
  },
};

export class UserError extends Error {
  constructor(message, status = 400) {
    super(message);
    this.status = status;
  }
}
export function assert(value, message, status = 400) {
  if (!value) throw new UserError(message, status);
}
export function tableSpec(table) {
  assert(Object.hasOwn(tables, table), "Unsupported content table");
  return tables[table];
}
export function validKey(table, key) {
  const keys = tableSpec(table).keys;
  assert(
    key &&
      typeof key === "object" &&
      !Array.isArray(key) &&
      Object.keys(key).length === keys.length,
    "Invalid record key",
  );
  for (const field of keys)
    assert(
      Object.hasOwn(key, field) &&
        Number.isSafeInteger(key[field]) &&
        key[field] > 0 &&
        key[field] <= id.max,
      "Invalid record ID",
    );
  return Object.fromEntries(keys.map((k) => [k, key[k]]));
}
export function validatePatch(table, patch) {
  const fields = tableSpec(table).fields;
  assert(
    patch && typeof patch === "object" && !Array.isArray(patch),
    "Expected field values",
  );
  assert(Object.keys(patch).length > 0, "No fields supplied");
  for (const [key, value] of Object.entries(patch)) {
    assert(Object.hasOwn(fields, key), `Field ${key} cannot be edited`);
    const rule = fields[key];
    assert(typeof value === rule.type, `${key} must be ${rule.type}`);
    if (rule.type === "number")
      assert(
        Number.isFinite(value) &&
          value >= rule.min &&
          value <= rule.max &&
          (!rule.integer || Number.isInteger(value)),
        `${key} must be ${rule.integer ? "an integer" : "a number"} from ${rule.min} to ${rule.max}`,
      );
    else
      assert(
        value.length <= rule.maxLength && !/[\x00-\x1f]/.test(value),
        `${key} exceeds its length or contains control characters`,
      );
  }
  return patch;
}

// Numeric driver representations may differ, but names such as "001" stay distinct.
function equalValue(a, b) {
  if (a === b) return true;
  if (
    (typeof a === "number" &&
      Number.isInteger(a) &&
      !Number.isSafeInteger(a)) ||
    (typeof b === "number" && Number.isInteger(b) && !Number.isSafeInteger(b))
  )
    return false;
  if (typeof a === "number" && typeof b === "string" && b.trim() !== "")
    return Number.isFinite(a) && a === Number(b);
  if (typeof b === "number" && typeof a === "string" && a.trim() !== "")
    return Number.isFinite(b) && b === Number(a);
  return false;
}
export function equalRows(a, b) {
  if (a === undefined || b === undefined) return false;
  if (a === null || b === null) return a === b;
  const keys = Object.keys(a);
  return (
    keys.length === Object.keys(b).length &&
    keys.every((k) => Object.hasOwn(b, k) && equalValue(a[k], b[k]))
  );
}
export function makeChange(table, key, before, patch, mode = "update") {
  const spec = tableSpec(table);
  key = validKey(table, key);
  // docs/pok/catalog-policy.json reserves these sixteen class merchants.
  // Their stock must remain reproducible through canonical restock/era tooling.
  const curatedMerchant = (value) =>
    Number(value) >= 99300 && Number(value) <= 99315;
  assert(
    !(table === "merchantlist" && curatedMerchant(key.merchantid)),
    "Class-hub stock is managed by docs/pok/catalog-policy.json. Use the reviewed catalog/restock workflow.",
  );
  if (table === "npc_types") {
    const curatedNpc = key.id >= 997900 && key.id <= 997915;
    const changesMerchant = Object.hasOwn(patch ?? {}, "merchant_id");
    assert(
      !(
        (curatedNpc &&
          (changesMerchant || Object.hasOwn(patch ?? {}, "class"))) ||
        (changesMerchant &&
          (curatedMerchant(before?.merchant_id) ||
            curatedMerchant(patch.merchant_id)))
      ),
      "Class-hub assignments are managed by the catalog policy. Use the reviewed catalog workflow.",
    );
  }
  assert(
    ["update", "insert", "delete"].includes(mode),
    "Unsupported operation",
  );
  assert(
    mode !== "insert" || spec.insert,
    "Inserting this record type is not supported",
  );
  assert(
    mode !== "delete" || spec.remove,
    "Deleting this record type is not supported",
  );
  assert(
    mode === "insert" ? before === null : before !== null,
    "Record existence changed; refresh and try again",
    409,
  );
  if (mode !== "delete") validatePatch(table, patch);
  if (before)
    for (const [k, v] of Object.entries(key))
      assert(equalValue(before[k], v), "Snapshot does not match record ID");
  const after = mode === "delete" ? null : { ...before, ...key, ...patch };
  if (after) {
    for (const [low, high] of [
      ["mindmg", "maxdmg"],
      ["mincash", "maxcash"],
    ])
      if (low in after && high in after)
        assert(
          Number(after[low]) <= Number(after[high]),
          `${low} cannot exceed ${high}`,
        );
    if (table === "loottable_entries" && Number(after.droplimit) > 0)
      assert(
        Number(after.mindrop) <= Number(after.droplimit),
        "Minimum drops cannot exceed drop limit",
      );
    if (table === "npc_types" && "name" in patch)
      assert(patch.name.trim().length > 0, "NPC name cannot be empty");
  }
  assert(!equalRows(before, after), "No change to stage");
  return { table, key, before: before ? { ...before } : null, after };
}
export const reverseChange = (change) => ({
  ...change,
  before: change.after,
  after: change.before,
});
export const changeIdentity = (change) =>
  `${change.table}:${JSON.stringify(validKey(change.table, change.key))}`;
export function changedFields(change) {
  return Object.keys(change.after ?? change.before).filter(
    (k) => !equalValue(change.before?.[k], change.after?.[k]),
  );
}
export function identifier(value) {
  assert(/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(value), "Invalid SQL identifier");
  return `\`${value}\``;
}
export function sqlValue(value) {
  if (value === null) return "NULL";
  if (typeof value === "number") {
    assert(Number.isFinite(value), "Invalid SQL number");
    return String(value);
  }
  assert(typeof value === "string", "Invalid database value");
  return `CONVERT(X'${Buffer.from(value, "utf8").toString("hex")}' USING utf8mb4)`;
}
export function sqlPreview(changes) {
  const lines = [
    "-- REVIEW ONLY: apply this change set through NPC Admin for drift checks, backup and atomic rollback.",
    "-- These statements are documentation, not a standalone deployment script.",
  ];
  for (const c of changes) {
    tableSpec(c.table);
    if (c.before === null) {
      const keys = Object.keys(c.after);
      lines.push(
        `INSERT INTO ${identifier(c.table)} (${keys.map(identifier).join(", ")}) VALUES (${keys.map((k) => sqlValue(c.after[k])).join(", ")});`,
      );
    } else {
      const where = Object.entries(c.before)
        .map(([k, v]) => `${identifier(k)} <=> ${sqlValue(v)}`)
        .join(" AND ");
      if (c.after === null)
        lines.push(`DELETE FROM ${identifier(c.table)} WHERE ${where};`);
      else
        lines.push(
          `UPDATE ${identifier(c.table)} SET ${changedFields(c)
            .map((k) => `${identifier(k)} = ${sqlValue(c.after[k])}`)
            .join(", ")} WHERE ${where};`,
        );
    }
  }
  return `${lines.join("\n\n")}\n`;
}
export function parseLocation(text) {
  const match = String(text)
    .trim()
    .match(
      /^(?:Your Location is\s+)?(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)[.!]?$/i,
    );
  assert(match, "Paste /loc as Y, X, Z (for example: -185, -1506, 2)");
  const location = {
    x: Number(match[2]),
    y: Number(match[1]),
    z: Number(match[3]),
  };
  validatePatch("spawn2", location);
  return location;
}

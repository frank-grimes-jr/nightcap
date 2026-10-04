import { readFile } from "node:fs/promises";
import {
  createPool,
  rows,
  zones,
  searchNpcs,
  npcDetails,
  items,
} from "../api/database.mjs";
import { tables } from "../api/domain.mjs";
const config = JSON.parse(
  await readFile(new URL("../config.local.json", import.meta.url), "utf8"),
);
const pool = createPool(config.targets.find((t) => t.id === "local"));
try {
  const schema = await rows(
    pool,
    "SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE()",
  );
  const missing = [];
  for (const [table, spec] of Object.entries(tables))
    for (const field of [...spec.keys, ...Object.keys(spec.fields)])
      if (
        !schema.some((c) => c.TABLE_NAME === table && c.COLUMN_NAME === field)
      )
        missing.push(`${table}.${field}`);
  const found = await searchNpcs(pool, { q: "Sortre" });
  const detail = found[0] ? await npcDetails(pool, found[0].id) : null;
  console.log(
    JSON.stringify(
      {
        missing,
        zones: (await zones(pool)).length,
        found: found.map((n) => ({ id: n.id, name: n.name })),
        detail: detail
          ? {
              spawns: detail.spawns.length,
              lootGroups: detail.lootGroups.length,
              merchantItems: detail.merchants.length,
            }
          : null,
        itemSearch: (await items(pool, "Rusty Scythe")).length,
        engines: await rows(
          pool,
          "SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN ('npc_types','spawn2','loottable','loottable_entries','lootdrop','lootdrop_entries','merchantlist','zone_state_spawns')",
        ),
      },
      null,
      2,
    ),
  );
} finally {
  await pool.end();
}

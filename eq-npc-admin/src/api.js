export async function api(url, body) {
  const response = await fetch(
    `/api${url}`,
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-NPC-Admin": "1" },
          body: JSON.stringify(body),
        },
  );
  const result = await response.json();
  if (!response.ok) throw new Error(result.error ?? "Request failed");
  return result;
}
export const label = (value) =>
  ({
    npc_types: "NPC template",
    spawn2: "Spawn location",
    loottable: "Loot table",
    loottable_entries: "Loot group",
    lootdrop_entries: "Loot item",
    merchantlist: "Merchant stock",
    hp: "HP",
    AC: "Armor class",
    mindmg: "Minimum damage",
    maxdmg: "Maximum damage",
    respawntime: "Respawn seconds",
    variance: "Respawn variance",
    pathgrid: "Path grid",
    spawngroupID: "Spawn group",
    loottable_id: "Loot table ID",
    merchant_id: "Merchant ID",
    probability: "Probability %",
    chance: "Chance / weight",
    droplimit: "Maximum drops (0 = unlimited)",
    mindrop: "Minimum drops",
    item_charges: "Charges",
    equip_item: "NPC equips item",
    heading: "Heading (0–511)",
    d_melee_texture1: "Primary weapon model",
    d_melee_texture2: "Offhand weapon model",
  })[value] ?? value.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());

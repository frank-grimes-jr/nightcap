# ADR 0040: Classic East Commonlands service and travel hub

Accepted September 20, 2026 for QA after owner approval of the tunnel proposal.

Move existing service spawn rows, preserving NPC identities, appearances, stock
and price policy. Add 22 native click doors; retain original PoK routes and add
adjacent return books. Reserve global door IDs40600..40621 and local door IDs200+
with all-version collision guards. New hub doors require normal 3D click range.

Use native `ecommons_assets.txt` to import `poknowledge_obj`; compensate the Grobb
model's local offset. Retire only the pinned newer Nektulos EQG to select existing
classic S3D geometry, and select the matching server map/nav/water alias. The
installer holds the exact archive against write/delete through retirement and
restores through verified temporary bytes plus atomic non-replacing publication.

Set new starts and safe arrival to EC, but preserve existing binds and positions.
Repair Ancient Attunement in place: AA2220/rank22200 keep ownership and cooldown,
use General/type1/category9, representable unused spell42604/Teleport83, and
SID22200 types1/2/4 for title/hotkey/description. Preserve its unrelated type6.
Spell99001 remains untouched for audit; its old SummonPet effect and uint16
truncation cannot implement recall. Never rewrite player home binds as a shortcut.

SQL generation rejects full-row drift, unsupported engines/triggers, mixed spawn
groups, changed start policy and recall references. Invalidate only scoped NPC
saved states after graceful shutdown. Manual QA gates main promotion.

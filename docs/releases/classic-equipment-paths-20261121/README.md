# Classic equipment acquisition and effect release

Deployed November 21, 2026 from main PR523 / 688932e2 as `classic-equipment-paths-20261121-v1`, after the completed ornament server/wiki rollout. The owner explicitly authorized this sequential main/server promotion; ordinary-player acceptance remains open.

Adds effects to 149 stock families / 596 quality definitions across crafted/racial armor, enchanted jewelry, class quests, Ro armor and named drops. Corrects only Temple of Solusek Ro's expansion field from 1 to 0. Existing healing strength, custom augments, occupied effects, raw stats, recipes, quest reward qualities and AA ranks are preserved. See the full item catalog and QA.md.

The ornament shipping binary bceda35d was reproduced exactly. All 212 pressure, 312 defense and 112 offense pairs were rerun with byte-identical outcomes to the earlier validated run. Seven content and 15 repository guide checks pass. Native measurements do not establish full encounter AI, visual behavior or player acceptance.

Fresh successor rehearsal passed forward, replay, rollback and reapply. The resulting item cache changes exactly 596 of 324,796 records and preserves the other 324,200, including every ornament definition. Cache SHA256: `63bb841bae58642adde3bb47c5a0e622d5a0b25b32a75bb6025483adbb8bbd74`. Full-row guards and one atomic item/zone transaction remain in force. Historical negative drift controls are in atomic-rehearsal.json.

Activation used a zero-player drain, clean whole-runtime stop, fresh stopped backup, saved-state and market verification, paired cache boot and reopening. Independent verification confirms 12 healthy workers, zero restarts/errors and open access. The ornament image 50bcce34, world 9726ce1c, zone bceda35d, spell cache and signed client 2026112101 remain paired. Reconnect; no new client download. Do not replay activation or restore a player snapshot. Any recovery must preserve subsequent play and use fresh guarded content state.

Current evidence: production-preflight.json, production-verified.json, runtime-after-ornaments.json, staged.json and promotion-main.json. Earlier candidate-preflight.json and pre-ornament receipts are historical, not current cache pins.

Wiki package `20261121-classic-equipment-paths-v4` is prepared over the verified public `20261121-visible-ornaments-v1`: 7 outputs change and 624 remain identical. All 24 publication-source Python checks, equipment checks and search pass. Publication is pending; this server instruction did not authorize it. Historical refresh drift remains review-required, and no ledger was blindly advanced.

# In-game QA: three normal items

Pending; perform only after the matched zone/quest release is installed on the
selected test server. Record server/client hashes, character, item IDs, screenshots,
before/after inventory, receipt IDs and skipped cases. Use disposable QA items.

1. In East Commonlands, hail Artisan Veyra 999820 in the tunnel workshop. Request
   the free Reforging Box 900620. Hail, `normal`, `base`, and a repeat box request
   should explain three Normal/Base and four higher-tier copies.
2. Put the box in a main inventory slot. Verify four slots and Combine. Place
   three ordinary Cloth Caps 1001 inside, fourth slot empty. Combine: exactly one
   Polished Cloth Cap 201001 inside, no fee/failure, reusable box retained.
3. Repeat for three catalog hunt Base items 940024 -> one 940025. Inspect the
   actual source/target names and stats before the test. Different slots, including
   an empty first slot, should also work; output occupies a consumed slot.
4. Test two and four normal copies, mixed item IDs/qualities, a normal item with
   no matching Polished definition, and customized/socketed items. Every rejection
   retains every input and creates no receipt. Remove customization and retry.
5. Four 201001 -> one 401001, four 401001 -> one 601001; four 940025 -> one
   940026, four 940026 -> one 940027. Three higher-tier copies must still reject.
   Top-tier and dungeon rewards (960000 range) must reject at both three and four.
6. Fill other inventory slots; a valid combine still returns into the box. Test
   bound and unbound ingredients. Close/reopen, zone and relog: exactly one output
   and the box persist, consumed inputs stay gone, binding persists, one receipt.
7. If eligible stackable/charged families exist on the target, test three normal
   units in one stack and split stacks; output is one unit. Three charged physical
   copies count as three, not their charges. Record any unavailable fixture family.
8. Test combat/casting/trade rejection, rapid Combine clicks and a reconnect.
   Never retry an uncertain result. On an isolated server, disable hunt/upgrade
   state to confirm rejection preserves inputs; never inject faults into live SQL.
9. Use `#zoneforge`: three Base, four Polished, four Exalted remain its costs.
   Check an ordinary tradeskill combine still behaves normally. Use the box in
   another zone. Confirm existing client assets suffice.
10. Assess ordinary gear progression with representative solo builds. Verify the
    new three-normal entry point feels worthwhile without trivializing encounters.

These checks do not mark the older full item-upgrade QA plan accepted. Main/live
promotion and in-game acceptance are separate from automated fixture results.

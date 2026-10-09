# Classic hunt and forge

Approved and deployed October 9, 2026 under explicit owner authorization. Main `77f5d63` and the matching production build are live on OVH. [Deployment, preservation and recovery evidence](PRODUCTION.md). Manual gameplay acceptance remains open.

Forty-eight audited Classic combat zones have one new augment and one new wearable family. There are 384 droppable variants, plus 64 definitions reserved for the eight access-check zones. The 21 city concepts and noncombat hubs remain outside the acquisition pool. See [the original approved catalog](approved-catalog.json), [exact new item rows](generated/items.json), and [zone/source audit](generated/audit.json).

| Family roll per eligible death | Base | Polished | Exalted | Ascension |
|---|---:|---:|---:|---:|
| Augment: 0.5% | 60% | 30% | 8% | 2% |
| Gear: 0.5% | 60% | 30% | 8% | 2% |
| Final chance per family and tier | 0.30% | 0.15% | 0.04% | 0.01% |
| Mean eligible kills per family and tier | 333.3 | 666.7 | 2,500 | 10,000 |

The two family rolls are independent, so one death can award both. Any particular family averages 200 eligible kills, with no guarantee or pity timer. Across both families the chance of at least one reward is 0.9975% per eligible kill. Existing named loot and legacy quality rolls remain unchanged.

The source audit permits 6,056 exact native spawn/NPC pairs, with zone-specific minimum levels and version 0 only. Kithicor additionally requires nighttime and an audited undead source. City services, merchants, quest hand-in NPCs, tunnel residents, pets, summoned clones, and restored dead NPCs do not roll. Native spawn identity prevents script-created copies of an otherwise eligible NPC type from qualifying. Plane of Fear's identical signal-only follower script was explicitly reviewed; its accepted content hash is pinned in the generator.

## Augments and power limits

The migration adds one type-22 socket to 2,290 eligible Classic drop armor definitions, preserving every existing socket. New six-location armor also carries one socket. Only head, arms, hands, chest, legs and feet accept these augments; all tiers can use them. Existing gear with no free socket or an incompatible mixed wear mask is left unchanged.

At wearer level 50 and above, effective heroic INT from these new socketed augments increases the item Spell Damage cap by `min(30, floor(total / 2))`. Heroic WIS does the same for Healing Amount. Recommended-level scaling, required level and class/race checks apply. Gear, other augments, buffs, tribute and AAs do not receive this special credit. Raw bonuses are totaled before the cap, independent of item order. Missing Spell Damage/Healing Amount is never granted by increasing the cap. NPC, bot and mercenary cap behavior stays unchanged.

Native heroic effects and attribute cap increases still apply, so combined HP, mana, mitigation and output must be evaluated together. The maximum +30 headroom takes a 250 cap to 280; in percentage mode the output multiplier changes from 3.50 to 3.80, an 8.57% increase before other effects. Throw Stone's direct Spell Damage addition also increases by at most 30 from this headroom. Automated stat measurements and manual encounter acceptance are separate evidence.

## Forging

Type `#zoneforge` outside combat with the cursor empty and trade, merchant and loot windows closed. The menu names every available upgrade. Each link consumes exactly three identical unequipped, unmodified copies from carried inventory/bags and places one next-quality copy in the first consumed slot. There is no fee, random failure, cross-family conversion or upgrade beyond Ascension. Socketed, dyed, ornamented, evolving or customized inputs are rejected.

Each choice is single-use and pinned to exact runtime item instances. The transaction locks and compares persisted inventory preimages, consumes all three, saves the output and writes a durable receipt in one InnoDB commit. Attunement is retained if any input was attuned. Uncertain commit or publication results quarantine the session and require reconnecting. No automatic retry can spend or grant twice.

The existing universal-trading policy remains in force, including for augments and attuned items. Raw SQL flags and instance binding are preserved. These new rewards have no merchant resale value even when FreeTrade is enabled.

## Activation and recovery

1. Use the production build manifest and reviewed patch over the fingerprinted live source. Preserve production authentication hardening; the older development/integration manifests are not deployment artifacts.
2. Stop target writers using the documented supervisor procedure, back up PEQ, and recapture target content using the source audit tool. Regenerate and compare the proposed SQL. The attached preimages are the October 9 capture, not a promise that a later target has not changed.
3. Apply `generated/install.sql`. It refuses reserved-ID collisions, existing feature ownership, nontransactional item storage and socket preimage drift. Acquisition remains disabled. Preserve all existing character, corpse, advanced-loot receipt and saved-state data.
4. Generate matching shared item memory, install the candidate binaries, apply `generated/activate.sql`, and start/reload the supported runtime. Zone source eligibility is cached on zone initialization. Verify the active Classic era through the existing era tool; do not alter expansion rules by hand.
5. Run [exact owner QA](QA.md). Access-check zones remain disabled. Lavastorm's existing signed-client readiness gate must remain intact.

Operational rollback is `generated/rollback.sql`, followed by a supported zone reload. It disables drops and forging while retaining item definitions, sockets, earned stats and forge/advanced-loot receipts. It intentionally does not delete player-owned rewards or replay old inventory snapshots. Removing the system's earned power after player activity requires a separately reviewed migration. Never roll back to binaries predating advanced-loot receipt support.

## Evidence

- [Measured native balance](BALANCE.md): 24 synthetic loadouts, bounded output caps and material HP/mana growth; encounter acceptance remains open.
- [Native loot and forge failure injection](inventory-native.json): actual production translation unit, with fake dependencies.
- [MariaDB rehearsal](mariadb.json): generated SQL, late-preimage rollback, exact native forge queries, receipt replay and operational rollback.
- [Production build manifest](production-build-manifest.json): the deployed five-binary set, retaining existing production hardening. [Combined development build](integration-build-manifest.json) and [original feature build](build-manifest.json) retain their historical candidate scope and were not installed.
- [Verification and integration review](VERIFICATION.md): checks, branch ancestry and remaining acceptance gates.
- `tools/tests/test_zone_hunt.py`: approved data, source exclusions, socket preservation.
- `tools/tests/test_zone_hunt_native.py`: actual death award, cap methods and recommended-level calculation, plus integration gates.

Automated checks do not establish client rendering, socket UI, encounter balance or manual gameplay acceptance. Those gates remain in QA.md.

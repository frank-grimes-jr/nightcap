# Server fixes candidate: in-game QA

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


This candidate packages five existing C++ fixes. It does not change spell/healing
caps, NPC HP, the live AA offering, character purchases or era configuration.
The balance study remains open. Test-to-main requires the owner's sign-off.

## Candidate behavior

| File | Trigger | Expected result |
|---|---|---|
| zone/attack.cpp | A character uses a weapon allowed by a held secondary/tertiary class | Normal weapon damage works; race and required-level restrictions still apply |
| zone/mob.cpp | Native owner lookup runs on a registered extra pet | The pet retains its owner; an unregistered orphan still detaches |
| zone/client_packet.cpp | Attack/qattack is sent to multiple pets or extra pets without a primary | All eligible pets receive native attack orders; command spam never creates immediate swings |
| zone/spells.cpp | A beneficial AA spell is cast on its owner | Its native duration is retained; ordinary long-lived self buffs remain long-lived |
| zone/aa.cpp | Owned AAs reload | Profile entries agree with accepted native ranks, and old profile entries are cleared |

## Activation boundary

The source patch, original/candidate hashes and isolated build evidence accompany
this file. Before activation, preserve the current zone binary and configuration,
verify the candidate checksum, confirm all players have logged out, and switch
the zone binary during the agreed test window. Restart every zone and verify each
process started after the binary replacement. The preparation/build step does not
perform that switch or restart. Keep the original binary available for rollback.

No AA data projection or ownership-ledger migration belongs in this activation.
Do not change era rules by hand. If an era change is needed independently, use
era.json and the declarative era script under its existing agreement.

## 1. Held-class weapon damage

Use a disposable non-GM level-50 WAR/CLR/MNK in soldungb. Equip Balanced Tonfa of
Serenity 662038. Against a legal nearby NPC, confirm normal one-hand-blunt hits
deal damage separately from Flying Kick and Tiger Claw. Confirm those abilities
retain their independent cooldowns and that recommended-level scaling remains.

Repeat on WAR/CLR/WIZ: the Monk weapon must remain unusable. Ordinary Warrior
weapon 662035 must still work. Race-ineligible 5100 and required-level-65 item
24587 must retain their restrictions. Check an ordinary single-class melee
character and, if used on this server, a bot under its existing equipment rules.

## 2. Three-pet ownership and commands

Use a disposable non-GM level-50 MAG/NEC/SHM with Malachite 10015 and Bone Chips
13073. In a cleared area of soldungb near (-861, -1395, 104.88), cast Greater
Conjuration: Water 633, Invoke Death 443 and Frenzied Spirit 166. All three pets
must remain owned and visible after 12 seconds. Repeat with different summon
orders, replacement summons, dismissal and pet death.

Cast Burnout III 107 on the primary water pet; check the buff/haste and continued
presence of both extras. A zero-AA, unfocused control without Malachite must fail
the water summon; supplying it must consume one on success.

At roughly 80 units from a legal NPC, issue attack and qattack. All eligible pets
must approach and attack normally. Repeat at 500 units: pets must not gain an
attack order or deal immediate damage. Send four rapid commands; their frequency
must not create extra swings. Remove the primary pet and repeat at legal range:
the remaining Necromancer/Shaman pets must still respond.

Check backoff, follow, sit/stop/regroup, zoning, relogging and resummoning. Confirm
no orphan pets remain. Repeat primary-only behavior. Check a mezzed or illegal
target, a feared pet, familiar/target-lock pets, and LoS with its existing rule.
Charm, swarm and bot ownership paths require regression QA if used by the build.

## 3. Temporary AA buffs versus ordinary self buffs

On a disposable WIZ-capable test character in Plane of Knowledge, use the recorded
duration-inputs.json AA allocations or equivalent test grants. Cast Arch Shielding
67 and Resolution 314 separately; they should remain after 150 seconds and can be
clicked off. Activate Improved Twincast and Frenzied Devastation: check native
duration, charges, charge consumption and expiration.

Test the recorded Tenacity ranks with full and reduced health. Record HP/max HP
each tick and expiration, with a recovery plan for the high-rank drain. The shared
cooldown with Celestial Regeneration must remain. The separate level-50 Celestial
Regeneration rejection is not fixed by this candidate. Triggered AA subspells are
not broadly certified by the direct-rank duration fix.

## 4. Owned-AA reload

On a disposable character with legal Natural Durability purchases, record its rank
count, wallet, spent total and HP. Zone, camp/relog and reload through the normal
character path. The purchased count and effective bonus must agree, with no extra
profile entries or unexpected point change. Repeat on a zero-AA control.

Invalid/above-cap saved counts and stale-profile removal have isolated native
fault-injection evidence in aa-ownership-before/after.json.gz. Do not inject those
rows into an ordinary live character for this QA. This loader fix preserves
rejected stored rows; it does not clamp/refund them or install expansion caps.

## 5. Matched encounter checks

With fixed recorded gear and preparation, fight Lord Nagafen 32040 in soldungb and
Lady Vox 73057 in permafrost. Use zero and launch-maximum purchases: 135 points for
WAR/CLR/WIZ, 141 for WAR/CLR/MNK and 165 for MAG/NEC/SHM. These are candidate build
allocations, not the complete production AA offering. Record duration, minimum HP,
mana pressure, pet deaths, fear recovery, AA expiration and command behavior.

Success is correct mechanics and a reproducible record of remaining balance gaps;
these fixes do not promise every build wins. Compare the corresponding native
report and investigate material differences before numerical tuning or main
promotion. Record acceptance/failures per section and the candidate binary hash.

## Rollback

If the candidate causes a regression, log players out, restore the preserved zone
binary, restart every zone and verify process start times/checksum. Restore source
only against the recorded candidate hashes to avoid overwriting later edits.
This candidate makes no data migration, so a database-wide restore is not its
rollback procedure.

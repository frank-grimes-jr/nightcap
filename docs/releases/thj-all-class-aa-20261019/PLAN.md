# All-class AA catalog update — October 19, 2026

Implementation candidate, not a production deployment or balance acceptance.
Baseline: main73358d / October18 combined release,1160 ranks in408 families.

The owner requested review of the collected THJ data and an AA update for all16
classes, with balance work following. This pass expands paid native AA rank
availability against exact archived THJ family/rank IDs, preserves every released
rank and the recent pet/WPM ceilings, and restores Druid access to Healing Boon
from the released April20 patch. It does not treat an old matching name or ID as
proof that native effect values equal THJ's customized effect values.

## Evidence and decisions

- `thj-ranks.json` retains566 numeric identity/count records from the pinned
  public archive; `source-manifest.json` pins the archive and all16 class guides.
- Retained Google notebook AAData rows1–31 covers every class. It corroborates
  many choices but is recommendation prose, not a complete spell database.
- Released forum post2671 adds Druid Healing Boon; post2845 (May7) supersedes
  the May1 test proposal. Do not apply an older builder as newer patch behavior.
- Native identity, current class ownership, earned costs and prerequisites remain
  authoritative. Disabled duplicates, grant-only/reward/charged AAs, custom
  missing IDs and mismatched chains do not enter by name matching.
- No additional free Harm Touch, Lay on Hands or Hunter's Attack Power ranks.
  No arbitrary prerequisite waivers; blocked prefixes are reported explicitly.
- Retain fixed-damage execute/resource deferrals. Wizard Destructive Fury397
  receives a separate native audit; it is not the non-Wizard398 family.
- Bard Dance of Blades359 and Hastened Blades541 can now be enabled: the released
  AA duration classifier resolves the old permanent-buff objection. Preserve
  native2160-second base reuse and finite duration; archived900–1020 lacks
  a per-rank mapping and is not silently guessed.
- Preserve existing Spell Casting Subtlety25. May7 removal and replacement
  Silent Casting behavior need an earned-point/ownership migration decision;
  no saved points or purchases are silently erased by this catalog pass.
- Native effect values, free-rank policy and the exceptions in the generated
  report are deliberate differences, not claims of complete THJ parity.

## Implementation / acceptance

Generate a deterministic policy, native header, content-only Healing Boon class
migration, all16-class player list and full566-record disposition ledger.
Validate dependency closure, exact identities, all released ranks retained,
client strings/spell availability, all696 legal one/two/three-class masks, native
activation/cooldowns and dormant ownership. Rehearse SQL with isolated tables,
including idempotency, drift rejection and rollback preserving player rows.
No new spell, client binary, era, item or pet changes are part of this pass.

Before promotion to main/server: owner in-game QA per QA.md, reviewed current
production preimages and a matching zone binary. A new compiled policy requires
zone rebuild/restart; AA reload alone cannot install it. Preserve the pending
client-contract repair pairing; do not republish the incompatible old bundle.
Normal branch policy permits dev/test only until a new owner approval.

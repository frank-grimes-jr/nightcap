# Three class pets: QA candidate

September 19, 2026. One permanent summoned pet per held eligible class, one
ordinary pet window controlling the roster, and separate existing eight-slot
armor loadouts. Manual acceptance remains pending after the owner-authorized
[main source promotion](../main-promotion-20260920.md).

The server now assigns summons from original spell eligibility rather than the
multiclass-widened database columns. It saves all class pets, preserves the
class of suspended pets, and switches the single native pet window to a survivor.
Duplicate same-class summons cannot replace or add another pet. Native command
permissions and combat checks remain in force.

- [Exact owner QA](QA.md)
- [Verified server activation and recovery](ACTIVATION.md)
- [Architecture and rollback constraints](../../adr/0039-class-pet-roster-and-persistence.md)
- [East Commonlands assessment; no migration applied](../../pok/ecommons-tunnel-proposal.md)

## Automated evidence

Evidence summaries are in [native](native/); full inputs, outputs, build manifest
and logs remain in `E:\EQ_Local_Dev\artifacts\multiclass-pets-20260919`.

| Check | Result |
|---|---|
| Original catalog generator | 547 records; source SHA pinned; generated header matches |
| Compiled ownership policy / parser | 3 passed, including six class orders and shared-spell gates |
| Existing armor transfer tests | 2 passed |
| Skill lifecycle / atomic class release guards | Passed |
| Full zone/world build | Passed |
| Real native class × summon order matrix | 36 passed, 936 actions |
| Attack / Quick Attack and range restrictions | 8 passed, 32 commands |
| Legacy and class-keyed suspended-pet migration | 4 passed |
| Deliberate save failure in isolated clone | All three tables rolled back byte-for-byte; session quarantined |
| Final-build roster smoke / failure recheck | 26 actions passed; failure rollback passed |
| Independent final lifecycle review | No remaining blockers |

The full matrix and attack tests used diagnostic SHA
`ba5c8da4ffa6d9ff7435538e8e2efdb7cc9de62891fc3c60bf7c29ee99d24cf8`.
The final legacy suspended-pet repair, four migration cases, roster smoke and
failure rerun used
`620033790eeafbbab25cd5d8679c55a98f865bbb5f6d223b04919ff3f4e27d33`.
The level-64 shared-spell case is a mechanical persistence fixture, not a change
to the Classic level cap or available content.

Production candidate hashes:

- World: `f7db30da4c3c337637b6a42dce82dc0290818e7c692584652a4bb99fc13149cd`
- Zone: `ee0cc6ab7a83d2d538d6342273eb6fbfed8cc738a35cb0103090e1825435e2b4`

No new client files or schema migration are required. Matching source overlays
and candidate binaries are now active on the development server; the running
world and all eight zones were verified. See the activation evidence above.

## Recovery

Before activation, gracefully save/stop the server and back up the three pet
state tables (and the full database). Keep matching pre-release binaries and
source overlays. Extended active/suspended class keys are documented in ADR 0039.
An older binary deletes these keys on save: binary rollback alone is insufficient.
Preserve post-activation pet states for reconciliation before reverting. Never
drop the armor table or restore an old full database over newer player progress.

This release does not alter the existing balance policy, era lock, merchant
stock, or hub location. Three simultaneous pets need owner encounter QA before
main promotion; automated correctness tests do not establish encounter balance.

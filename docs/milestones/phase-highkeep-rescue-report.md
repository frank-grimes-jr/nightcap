# High Keep rescue candidate —2026-10-24

Current status, October27: the feature was deployed in the coordinated October25
release, preserved by October26, and its live enablement/source/runtime/schema/
map pairing is now reverified. Public guidance is published. This supersedes the
candidate-only disposition below; owner gameplay and balance acceptance stay open.
See `docs/dungeons/highkeep-rescue/live-verification-20261027-v3.json`.

Built: entrance suspicion/alarm, compact boss projection, zone-wide story hints,
Osargen follow/protection/healing, three fixed pursuer waves, leader handoff,
attempt recovery, and personal extraction completion with existing receipt claims.
Native tests, database rehearsal and terrain/navigation evidence are in
`docs/dungeons/highkeep-rescue/`. The latest wiki source has a separate candidate
with release labels, seven guide updates and generated High Keep guidance.

Deliberately omitted: permanent faction penalties, public-zone changes, new item
rewards, arbitrary teleport recovery, live deployment and a new client patch.

Remaining uncertainty: in-game doors/following, dialogue readability, encounter
pacing and combined maximum-legal-power balance. Initial tuning is explicit in
BALANCE.md. This phase creates a reviewable candidate; it does not establish live
availability or owner acceptance. Full native builddad1c575286b2dd4 passes with
the final source manifest; main/server and wiki publication remain separate
approval boundaries.

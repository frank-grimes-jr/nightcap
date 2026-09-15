# ADR 0009: model preparation through native casts and client posture

Date: 2026-09-12. Status: implemented in the isolated diagnostic.

Preparation is part of the encounter input. Cast ordinary eligible self-buffs in
declared order through native spell handling, record completion and mana costs,
then optionally recover HP/mana by sitting. Use ordinary client appearance packets:
`Client::Sit()` changes appearance but does not set the client `playeraction` used
by `IsSitting()` and regeneration. Confirm actual sitting during recovery and
standing before engagement. Initial appearance-only runs were rejected and replaced.

Keep one continuous native clock, resource state, buff list and cooldown state.
Spawn the enemy after preparation, without resetting player resources. Record
preparation on the absolute clock and combat with timestamps relative to engagement;
retain `combat_start_ms` so the relationship is explicit. The no-preparation path
preserves its prior construction order and behavior.

The first policy casts Arch Shielding, Resolution, Symbol of Naltron, Resist Magic
and the appropriate elemental resistance, then fully recovers. These are ordinary
CLR/WIZ buffs; it does not assume access to Clarity from globally modified spell
class fields. Native stacking and survival through recovery are verified, not
replaced by additive estimates. Explicit preparation order matters to later dispels.

Scope remains bounded: WAR/CLR/WIZ candidate gear, existing nuke/heal and burst
policy, no pets, no optimal preparation or rotation claim, and no full BiS claim.
Recovery begins from full unbuffed resources, representing one prepared attempt,
not sustained farming. Rejected casts receive at most three attempts; invalid or
uncompleted preparation fails the run instead of silently assuming its benefits.

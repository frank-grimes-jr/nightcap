# Pre-merge review, September 27

Scope: Monk/Beastlord unarmed combat and practical skill caps; base-strength
spell/heal additions; guarded existing-item migration; read-only cast diagnostic.
Casting-bar correction is explicitly not delivered by this candidate.

Correctness: independent review found and resolved empty-offhand, unarmed damage
table/bonus and skill-up cap gates. Native-method tests cover primary/secondary/
tertiary, classic/revamped fists, magic immunity, equipment and release controls.
The cap regression uses captured native levels 1, 2 and 50. End-to-end gameplay
remains a manual gate; fixtures do not claim an actual client combat parse.

Data safety: formula generation is shared across bootstrap, verification and
migration. Transactional preimage and afterimage guards are rehearsed, including
failure after UPDATE and stale rollback. Fingerprints deliberately pin names,
formula inputs and the two stats; unrelated columns are preserved but not drift
guards. The full 308,928-row clone restored exactly. Hosted data was read only.

Diagnostic safety: explicit PID and executable path/hash checks precede timer
reads. Only query/read process rights are requested. Packaged spell duration is
an arithmetic reference, not native spell RAM; expired samples are marked.

Structure/performance: small changes stay in existing combat/cap paths, with no
per-swing database lookup. Held-class scans are bounded by three classes. The
item planner is an offline bounded catalog operation, not a gameplay hot path.
No new runtime dependency, credentials or client binary edits are introduced.

Verification: 19 focused tests, lifecycle/special-attack checks, isolated SQL
fault/rollback tests and full world/zone compilation pass. Source hashes remain
stable; all final objects postdate source restaging. Current main was merged;
its release-note conflicts were resolved without changing native sources.

Verdict: ready for dev/test source promotion with the linked QA gates retained.
Not approval for main, production deployment, balance acceptance or closing the
casting-bar report. External cross-model review was declined by the owner.

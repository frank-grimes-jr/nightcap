# Native player pursuit controls

Date: 2026-09-12. The diagnostic now supports explicit `return_to_melee: true`.
This improves the candidate encounter controller; it does not certify full BiS
or authorize cap/NPC-HP tuning.

## What changed

In the prior 500-point durability-first Vox case, seed 1731, the character stood
still after separation while low-health Vox moved around the room. The run ended
at 900 seconds with both actors alive. Native pursuit through the client position
handler now ends that exact case in a kill at **271.30 seconds**, with 4,924 HP and
83 mana remaining. Level, gear, AA allocation, NPC stats and spell rules are identical.

The 52-case pursuit matrix uses the same fixed weapon/haste/AA cases as
`gear-aa-encounters.md`. Movement affected three Vox encounters:

| AA policy / budget / seed | Before | With pursuit | Position updates |
|---|---:|---:|---:|
| Balanced / 200 / 1731 | Kill at 343.85 s | Kill at 343.90 s | 608 |
| Durability-first / 500 / 1729 | Kill at 307.65 s | Kill at 251.85 s | 153 |
| Durability-first / 500 / 1731 | Timeout at 900 s | Kill at 271.30 s | 193 |

All 954 movement steps satisfy the declared speed bound and are applied by the
native client handler. No route failures occurred. The balanced-policy kill
counts from the previous report are unchanged; durability-first at 500 points
now kills Vox in all three tested seeds. These are exploratory samples, not
population win-rate estimates.

## Fidelity and controls

Native pathfinding supplies the route. The diagnostic excludes disabled,
zone-line and portal polygons, rejects partial/stuck/teleport routes, checks
segment line of sight against geometry, and submits positions in bounded steps.
It stops for casting, crowd control, zero native run speed, ready healing under
55% HP, or restored melee range/line of sight. It never makes the player AI-controlled
to obtain navigation. Native fear movement remains separate.

The step bound uses the existing NPC ground-motion conversion and the player's
native resolved run speed. The result models deliberate mesh-following pursuit;
it does not reproduce all client physics, collision hulls, jumping or strafing.
The first steps of the timeout control adjust height gradually to the mesh.
Client movement speed, vertical placement, and response latency require QA.

The first attempt exposed a fixture failure: position updates without movement
history triggered the native ghost detector, whose world-service notification
crashed the disconnected diagnostic. The completed implementation supplies
non-exempting synthetic history samples before position updates and periodically
while moving. It keeps anti-cheat checks enabled. A diagnostic-only linker guard
fails explicitly on unmodeled outbound world packets; no live connection is made.

With pursuit disabled, the new binary reproduces all 52 previous encounter
records byte for byte (including their native report hashes). All seven isolation
preflight checks and 137 Python tests pass. No production binary, live rule, NPC
row, game client, or running service was changed. The prior diagnostic binary is
retained as `/tmp/nightcap-balance-20260912/balance-zone-before-movement`.
The full pursuit matrix also replays byte for byte. The isolated account and
character tables remain empty.

## Evidence and reproduction

- `movement-build-manifest.json`: the new diagnostic binary, exact link arguments,
  source and reused-object hashes. The 130 pinned objects/archives retain the
  earlier limitation: this is not a fresh full-source rebuild.
- `movement-vox-inputs.json`, `movement-vox-result.json`, `movement-vox-check.json`:
  the exact prior timeout and its pursuit result.
- `movement-matrix-inputs.json`, `movement-matrix-results.json.gz`,
  `movement-matrix-check.json`: 52 exact inputs, full reports and movement checks.
- `movement-legacy-inputs.json`: unchanged-policy regression inputs for the new binary.
- `movement-guard-check.json` and `movement-evidence-manifest.json`: isolation checks,
  artifact hashes and replay/regression results.

Copy the four native build/runtime files to the existing isolated directory and
run `python3 build_native.py --reuse-adapters`. Use its build manifest to confirm
the binary matches the stored input matrix before replaying; the matrix runner
refuses a different binary. Copy `encounter_matrix.py` and the desired stored
matrix into the runtime, then execute:

```sh
python3 encounter_matrix.py --run --inputs movement-matrix-inputs.json --output NEW-pursuit-results.json.gz
```

Run one matrix driver at a time because it uses shared per-case scratch filenames.
Retrieve the output and validate complete case coverage and every movement
report, from `tools/balance/`:

```powershell
python verify_native_movement.py --native ../../docs/balance/movement-vox-result.json --output ../../docs/balance/movement-vox-check.json --require-movement
python verify_native_movement.py --native ../../docs/balance/movement-matrix-results.json.gz --matrix-inputs ../../docs/balance/movement-matrix-inputs.json --output ../../docs/balance/movement-matrix-check.json
```

Preparation, activated-AA policies, final combat-oriented BiS/acquisition review,
additional actor processing where needed, timestep sensitivity, more seeds and
focused in-game QA remain before final balance recommendations.

# Classic Lavastorm client prerequisite

September 20, 2026. The owner approved preparing an update for the separate QA
client only, then supplied `E:/EQ_Local_Dev/lavastorm.s3d`. The missing-source
blocker is resolved. **Assets are verified and staged, not signed or installed.**
Neither client was modified; no server restart or stock rotation occurred.

## Verified Inputs

| Asset | SHA256 |
|---|---|
| Supplied `lavastorm.s3d` (839,387 bytes) | `daa1053f71320e1f5882417f3dadc0b65c55fb64c75f3a806bceb57bbceb24c3` |
| Existing `lavastorm_obj.s3d` | `6476962179483d940cde99ef60fee43477d95c158aa28ccc1bc0e14d396b7b1f` |
| Revamped `lavastorm.eqg`, pinned retirement preimage | `86988d368570e218022c420a4fa4e9d67e258356295d6bb4419a2d5834ef0b3a` |

EQEmu's archive reader found the expected world, objects, lights and textures.
`azone` converted the terrain and object archive. The native map probe matches
installed `lavastorm_v0.map` exactly at world X=1389,Y=1014,Z=131 and four nearby
samples. Center ground is Z=125.24105072, offset 5.759; all five samples have 80
units of headroom. This does not prove client rendering.

Evidence: `E:/EQ_Local_Dev/artifacts/lavastorm-qa-20260920/` contains
`geometry/README.md`, `geometry/geometry-comparison.json`,
`geometry/archive-list.txt`, `assets/audit.json` and `input-verification.json`.
The latter verifies all 20 previous package inputs unchanged and records
original-client before/after fingerprints. Eighteen gameplay assets are staged:
the existing 16 plus both Lavastorm archives. Thirteen Python client-asset tests
and the full normal launcher Go suite pass. The pre-push full repository rerun
passes 62 tests with one existing opt-in database skip. Its first attempt lacked
Docker permission; the authorized scratch-database rerun passed.

## Pending Build

The offline npm cache lacked pinned `vue-tsc` 3.3.11. The online dependency
download was rejected because the approval service hit its usage limit; no
restriction was bypassed. Independent geometry review passed. Packaging review
initially stopped on the same usage limit, then completed with no actionable
findings before the owner-requested dev/test source promotion. This promotion
does not retry or claim the signed release, desktop build or client installation.

Original client, read only:
`E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2`.

Only approved installation target:
`E:/EQ_Local_Dev/artifacts/client-gameplay-20260919/client`.

1. Resume the approved build: run `npm ci --ignore-scripts` in the feature
   worktree's `eq-launcher/frontend`. Packaging source review is complete.
2. Re-run `artifacts/lavastorm-qa-20260920/verify-inputs.ps1`. Copy the verified
   QA proxy/bootstrap to the feature worktree's ignored `eq-client-dll/build/`.
   Preserve the previous configuration's exact LF bytes; Windows checkout CRLF
   must not create unrelated signed-file drift.
3. Generate unique signed QA release **2026092003**, after confirming it is still
   unused, from the staged assets and existing private QA seed. Never print or
   export the seed. Run normal and `qacandidate` Go tests, then `build-qa.ps1`
   into fresh `artifacts/lavastorm-qa-20260920/launcher/`. Do not overwrite an
   open or older launcher.
4. Verify all 22 signed files and both retirement pins. Install only through the
   QA controller/launcher, preserving journaled rollback and refusal of changed
   preimages. Never manually delete/rename the live EQG.
5. Confirm the 20 previous files are unchanged, both Classic archives match,
   the retired EQG backup matches its pin, and original-client hashes remain
   unchanged. Verify startup, then perform owner in-game QA below.

Regeneration into a new output directory now requires
`--lavastorm E:/EQ_Local_Dev/lavastorm.s3d` in addition to `--client` and `--output`
for `tools/client_gameplay_assets.py`. Unknown archive hashes are rejected.

## Earlier Source Search

The following clients contained revamped `lavastorm.eqg` and supporting archives,
but none contained Classic `lavastorm.s3d` during the initial search:

- `E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2` (original; leave untouched).
- `E:/EQ_Local_Dev/artifacts/client-gameplay-20260919/client` (approved QA target).
- `E:/EQ_Local/Client_RoF2/everquest_rof2` (owner-suggested read-only source).

The recursive search of `E:/EQ_Local` also found no ZIP/7z/RAR/ISO client archive;
the CABs present are DirectX redistributables, not game terrain.

The [FV Project zone repair listing](https://fvproject.com/index.php/Zone_Files)
describes a Classic Lavastorm package, but direct HTTPS retrieval failed with an
expired certificate and HTTP returned 500. Certificate checks were not disabled.
Do not substitute unverified geometry or rename away the current terrain before
the complete Classic replacement is available.

## In-Game Acceptance

Using only the updated QA client, verify Classic Lavastorm loads with textures,
visible ring stones and safe footing at world X=1389,Y=1014,Z=131. Walk around
the ring, zone out/back and check client logs for missing-world/texture errors.
Verify the existing EC hub and Nektulos still render correctly.

Keep `nightcap:classic_lavastorm_client_ready` absent until readiness applies to
**every client allowed to use the port**. One patched QA client is insufficient:
the gate is global, not per-client capability detection. Until explicitly
approved, Khalure must offer the other eight rings and reject stale
`ring lavastorm` links without movement. After rollout acceptance, recheck menu,
actual travel, arrival and era gating. The owner subsequently authorized
[main source promotion](../../releases/main-promotion-20260920.md), not client
installation, global readiness or manual gameplay acceptance.

Until then Khalure offers the other eight Classic rings. The map alias repair
does not remove this client prerequisite or constitute manual gameplay acceptance.

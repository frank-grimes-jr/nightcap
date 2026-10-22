# Classic robe publication — October 22, 2026

Historical game2026102201 publication. The owner later confirmed waist gaps;
[current correction2203](../waist-correction/README.md) supersedes these archives.

Owner instruction: **“Approved. move into main.”** This followed the concrete
candidate, exact native QA and request for signed live-QA publication. It
authorizes this main promotion and client publication before visual acceptance;
it does not waive future branch policy or establish completed player QA.

Source PR276 merged at `4661ddcd3ed6389fce8d9120358d4b6a2b157622`. Signed game
`2026102201` replaces only `global_chr.s3d` and `global4_chr.s3d` with the reviewed
candidate-08 pair. All 136 other descriptors/URLs, the current DLL/catalog pair,
manifest policy, tombstones and patch history are retained. No server restart,
SQL, protected reference-client or installed player-folder write was required.

Players close EverQuest completely, reopen the normal launcher and press Play.
Observers need the same update. [Native QA](../QA.md) remains pending for all
seven races/both genders, dyes, seams, animation, armor swaps and relaunch.

## Delivery evidence

- `signed-candidate.json`: shipped-key signature, exact executable preflight and
  the retained DLL/catalog pair verified before publication.
- `deployment.json`: ten Linux publication/recovery tests pass; both immutable
  archives precede the atomic channel replacement. All five service identities,
  images, restart counts/start times and top-level public controls are preserved.
- `hosted-verification.json`: all 138 HTTPS file hashes/sizes, shipped-key signed
  channel, complete retained history and actual hosted DLL/catalog pair verify.
- `wiki-publication.json` and `wiki-public-verification.json`: guarded publication
  `20261022-classic-robes-v1`, sixteen Linux recovery tests, pointer rollback
  rehearsal, all 465 public hashes/security headers and five private-route denials.
  Seven guides/search change; published Keeper content and catalog values remain.
- `wiki-review.json`: all 21 maintained guides and 432 generated routes reviewed.
  Local wiki suite: 21 pass/nine POSIX skips; six search and seven equipment checks
  pass. The POSIX cases pass on the deployment host.

Independent publisher review found an interruption gap during a partial channel
write. Recovery now accepts only exact candidate byte prefixes, rejecting foreign
partials and symlinks; channel/archive truncation regressions pass on Linux. No
remaining actionable blockers were found. Independent reviewer execution hit a
local sandbox temp ACL restriction; the Linux receipts, not that failed attempt,
establish the test result. The owner declined an optional additional model review.

The first wiki staging attempt lacked `nginx.conf`, a test-only fixture. Tests
stopped before public mutation. A fresh private stage included that fixture;
all sixteen tests passed before the guarded updater ran. Production Nginx
configuration was neither changed nor reloaded.

## Operator and recovery

`prepare.go` and `verify.go` run as isolated commands inside the `eq-launcher`
module to use its shipped manifest parser/trust and preflight contract. The
private signing seed stayed local; only public signed payloads and operators
were uploaded. The exact private remote stage is
`/opt/nightcap/releases/classic-robes-20261022-v2`.

`publish.py` takes the production deployment lock, pins the old/new channel and
both archive hashes, verifies inherited assets, and rejects concurrent drift.
Re-running with the same inputs is idempotent. Never rerun it over a newer public
release. `recovery.json` records both exact prior signed archive descriptors,
including their HE90 helmets. Recovery uses a **higher** signed counter with
those two files and the current unrelated manifest assets/DLL/catalog; never
lower player checkpoints, restore player settings, or restore the database.

Native rendering and owner gameplay acceptance are separate from these delivery
checks. No visual-resolution claim is inferred from signatures or offline previews.

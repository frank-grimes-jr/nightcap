# Coordinated hosted update — September 20, 2026

Status: deployed for owner QA. The owner asked to deliver pending main server
and client patches together and include both in main. Release source `8e7619b`
integrates main `014978f` with the production launcher/hosting branch. This
specific promotion retains all remaining manual QA gates; it does not change
the normal approval requirement for future gameplay promotions.

Launcher 0.2.1 and signed release 2026092004 are available at
[the production download](https://play.nightcapgame.org/nightcap-friends.zip).
Close the old launcher, extract the new ZIP, select the existing supported game
folder and use Check for updates -> Install update -> Play.

## Scope and acceptance

Merge the production infrastructure with main, build all five native executables
from a fresh isolated source tree with the production credential-log hardening,
and publish launcher 0.2.1 / signed client release 2026092004 with 22 managed
files and exact-hash retirement of both revamped Nektulos and Lavastorm EQGs.
Keep the existing signing authority; no private keys are uploaded.

The initial hosted snapshot already contains living-economy schema and quests,
but its older native world/zone lack that implementation. Replace the paired
runtime without rerunning schema/content migrations or replacing hosted player
data. Inspect the hosted three-argument routine, resident afterimages and quest
hashes before activation. A world restart rotates finite stock by design.

## Deployment and rollback plan

1. Run packaging tests, native ELF contract and crypto self-test, and independent
   integration review. Record source and artifact hashes.
2. Stage the image and client package on OVH. Retain the current image and public
   generation. Verify staged hashes before stopping services.
3. Stop gateway/game gracefully, create and validate a consistent on-host DB
   backup, and record preservation fingerprints. Replace only reviewed runtime
   inputs; retain private configuration, accounts and character progress.
4. Start the matching world/zones. Verify health, economy epoch, preservation
   fingerprints and native WSS handshakes. On failure restore the previous image
   and any changed runtime files; do not restore the full DB over later progress.
5. Publish immutable client assets and the replacement launcher ZIP, then replace
   channel metadata last. Verify the hosted signature and every file hash.

Older launchers can still Play a valid cached release. Minimum launcher 0.2.1
is enforced when fetching the new manifest, so it does not prove all clients
updated. Keep `nightcap:classic_lavastorm_client_ready` absent until rollout and
owner rendering/travel QA pass. Full native login, combat, economy balance and
ten-player acceptance remain separate from transport/hash tests.

GitHub Actions deployment is not implemented by this manual release. A push to
main alone does not update OVH. Players receive built signed artifacts from the
hosted channel, not source files pulled directly from GitHub.

## Completed verification

- All five native binaries built from a fresh isolated tree; source fingerprints
  remained unchanged during compilation. The production hardening patch applied
  after normalizing Windows line endings in staging. World contains the current
  three-argument market call; native crypto self-tests passed locally and on OVH.
- Repository suite: 62 passed, one existing opt-in skip. Normal, production and
  desktop/production Go suites and production vet passed. Frontend built; npm
  audit reported zero advisories. Four Linux production checks and the Compose
  contract passed. Independent review findings were fixed; three mocked activation
  and four publication/interruption rehearsals passed.
- All 33 managed runtime files and 30 resident afterimages already matched; no
  quest replacement or schema/content migration ran. The procedure has three
  inputs, an existing definer and runtime EXECUTE access.
- The on-host backup validated to 444,884,409 uncompressed bytes. All eight
  account/character/inventory/currency/class/AA/merchant/trade fingerprints remain
  identical. Market epoch moved from 1 to 2: ten finds, six sales and four buys,
  all quantity one. Game restart count is zero.
- Actual running executable hashes match for login, world, UCS and all 12 zones.
  The live signature, all 22 file hashes and launcher ZIP hash pass. Native WSS
  handshakes pass on login/world/UCS/zone ports 5998/9000/7778/7000. This is transport
  verification, not account/gameplay acceptance.

| Artifact | Identity |
|---|---|
| Game image | `nightcap-game:release-2026092004` |
| Image ID | `sha256:f5fbf96becf229d8d55f100c6bbb658e105d8831cfd56d2da05ccb0e25163b59` |
| Running world SHA256 | `5e8d7d602b7108873d3ddda3e5e12ada71ce50fe15f32f63c408d4fcfdcd3057` |
| Running zone SHA256 | `6dd9b73c8a682ef200023519a7dd866b3bcefe37617576703bec63e6d6e15f4c` |
| Launcher ZIP SHA256 | `7171f9edf529279ae559838729fb3d72dc9a28cddbfdb5cb22f46d75107067cb` |
| Channel SHA256 | `e0a86aa6afe43383397f3a507ae365d17774cb072fd70cd0f03c35bd6f2e98b2` |
| Manifest expiry | `2026-10-20T19:05:51Z` |
| Signing authority | unchanged `production-4acb02e67aeb0b51` |
| Backup SHA256 | `3937b591b5c2ee61b9956a5c91de481eb3c2dbab0f9614a6131496caa91098ec` |

Backup and before/after audits remain on OVH under
`/opt/nightcap/releases/server-2026092004/`. Local build fingerprints, review
rehearsals and hosted smoke evidence are in
`E:/EQ_Local_Dev/artifacts/production-nightcapgame-20260920-r4/`.
The previous image remains available as `nightcap-game:production-candidate-20260920`;
it is the recovery baseline and still lacks native economy support. Image rollback
does not undo stock rotation and must not overwrite later player progress.
The local QA server and both workspace client installations were left unchanged.

## Owner in-game QA

Download and extract the replacement launcher, select the existing approved game
folder, then Check for updates, Install update and Play. Confirm existing character
ownership and inventory, silent UI activation, three inventory classes, AA names
and class column, owned-pet armor equip/remove and melee continuing while casting.
Visit the East Commonlands tunnel: confirm the class/merchant hub, all six residents
and normal-account finite-stock purchases/sales using the exact
[economy cases](../economy/QA.md) and [resident cases](../economy/residents/README.md).
Confirm zoning/chat and death removing beneficial buffs. Classic Lavastorm rendering
and landing need separate owner verification before its global travel gate opens.

## Publication recovery

The publisher validates immutable files before changing public pointers and
restores previous public files if replacement fails before channel commit.
After abrupt process/host interruption, inspect the public channel hash first.
If it is the new channel, retain that monotonic release and complete/verify its
matching ZIP and assets. If it is still the old channel, the previous ZIP/guide
can be restored from `releases/2026092004/previous-public` before a reviewed retry.
Do not blindly rerun into existing immutable destinations. Once clients have seen
a newer release, client rollback requires signing a higher release number with
the desired corrected content; decreasing the channel number is not a valid rollback.

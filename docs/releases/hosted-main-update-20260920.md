# Coordinated hosted update — September 20, 2026

Status: preparing; not yet deployed. The owner asked to deliver pending main
server and client patches together. Release input is main `014978f` plus the
production launcher/hosting branch, with all remaining manual QA gates retained.

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

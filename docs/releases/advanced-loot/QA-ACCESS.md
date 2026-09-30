# Isolated advanced-loot QA access

Date: 2026-09-30. **Historical isolated plan; superseded by explicit main/live
deployment authorization. This local cutover was not executed.**

The [candidate services](gameplay-qa.json) boot successfully. Client access is
deliberately gated: RoF2 needs world port 9000, currently published by
`akk-stack-eqemu-server-1`. Stopping that container disconnects local players.
Approval was sought for that local interruption. The owner instead authorized
direct main/live deployment; this historical proposal is not a pending request.

## Prepared candidate

- PR at preparation time: <https://github.com/frank-grimes-jr/nightcap/pull/91>,
  draft to `dev`; subsequently merged to main under the live-test authorization.
- Candidate container: `nightcap-advloot-qa-20260930`.
- Runtime: `/opt/nightcap-advloot-qa` inside that container.
- Database: `nightcap_advloot_qa_20260930`; its separate user has grants only there.
- Client and launcher: `E:/EQ_Local_Dev/artifacts/advloot-20260930/qa/`.
- Offline signed release: `2026093005`, with all 46 files verified.
- Fixture accounts: `advloota`, `advlootb`. Credentials and the QA database
  secret are kept in the access-restricted `advloot-private-20260930` artifact
  directory, outside Git and the distributable package.
- Client target: `127.0.0.1:15998`. The container publishes UDP 15998 to 5998,
  while its client login listener intentionally uses unpublished UDP 15997.
- Zone: East Commonlands, UDP 17000. World and login communicate internally.

The original `Client_RoF2_Dev` installation is not a QA destination. The QA
database has no copied player data. Its quest directory contains only canonical
hand-in helpers, so production quest acceptance still requires explicit fixtures.

## Proposed switch after approval

1. Recheck the live and QA container identities, running binaries, published ports
   and active work. Capture which live services were running. If another task
   changed either environment, reconcile that state before proceeding.
2. Prepare a replacement task-owned QA container from the same image, named
   `nightcap-advloot-qa-access-20260930`. Retain the original QA container as the
   recovery copy; do not delete it. Preserve its runtime, configuration and the
   separate database before moving access. Handle credential-bearing copies only
   in the private artifact directory. Verify the staged four binaries against
   [the build manifest](server-build.json).
3. Configure the replacement with the same isolated database and runtime, client
   login UDP 5998, and loopback-only host bindings for UDP 9000, 15998 and
   17000–17009. Keep world/login communication internal. Do not expose public
   interfaces, use `peq`, copy production characters, or run the migration again.
4. Stop the original QA container and the approved local live game-server
   container. Leave MariaDB and unrelated services running. Start the replacement
   QA container and its login/world/ecommons services.
5. Verify running binary hashes, world registration, zone boot, the intended
   published ports and isolated database identity before opening the QA launcher.
   Enter with a fixture account and confirm the server name is
   `Nightcap Advanced Loot QA (isolated)` before creating a character.
6. Run [the exact native acceptance matrix](QA.md), recording screenshots,
   character IDs, hashes and each result. Startup alone does not close those gates.

## Restore local live access

Stop the task-owned access container so it releases the host ports. Restore the
original live container to its recorded prior running state, and verify its login,
world and zones. Preserve the QA database, receipt rows, logs, runtime and both QA
containers for investigation; do not import QA state into `peq` or delete receipts.
Restore live access on a failed cutover as well as after the owner's QA session.

This restoration returns access to the unchanged live environment. It does not
prove an older gameplay binary can safely consume new advanced-loot checkpoints.
Any future production downgrade still needs the receipt-aware recovery review
described in [the implementation record](README.md).

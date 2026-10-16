# Paired native rollout helper

This helper is prepared for the owner's explicitly authorized tradeskill live-QA
release. It has not contacted production during development. Stage it at
`/opt/nightcap/releases/tradeskills-20261013` and run under the existing deployment
and GM maintenance locks through its CLI.

1. `preflight` verifies the reviewed live binary baseline, builds an image that
   changes only `bin/zone`, checks dependencies/native contracts, captures current
   support services, public entrypoints, quests, content and rules, and takes a
   verified gzip backup. The observed prior restart count may be zero or one.
2. `activate` closes the gateway, gracefully stops the game, captures stopped
   player/custom table fingerprints, starts the candidate, and requires zero
   candidate restarts. It writes `evidence/activated-closed.json` and **keeps the
   gateway closed**.
3. The separate client publisher publishes the paired signed release while the
   game remains closed to players.
4. `open` verifies the same candidate process start/container, unchanged stopped
   player/custom data, supporting services, quests, content and rules. It requires
   the exact signed client channel and all signed release assets. Only
   `channel.json` may change among the existing runtime helper's public
   entrypoints (`channel.json`, `launcher-channel.json`, `nightcap-friends.zip`,
   `guide.html`). It records the access boundary before opening the gateway.
5. `report` verifies the paired runtime/publication after access. It does not
   compare player data with a pre-access snapshot because play may have resumed.

The immutable `manifest.json` must include:

- `base_binaries`: all five reviewed live SHA-256 hashes, including the current
  divine-summon `shared_memory` loader; a newer or older unreviewed baseline fails.
- `binaries`: either the candidate `zone` hash alone or the full five-binary set
  with every other binary equal to the reviewed baseline.
- `runtime_helper_sha256`: the existing retained `runtime_ops.py` hash.
- `client_release` and `client_channel_sha256`: the paired signed generation.
- `files`: hashes of all staged inputs, including `zone`, `rollout.py`,
  `test_rollout.py`, and `client-verification.json`.

`client-verification.json` is the output of the existing signature verifier run
against the staged signed publication and the previously shipped production
public key. Required fields are `release`, `channel_sha256`, positive
`verified_files`, and `signature: "valid against shipped production public key"`.
This report is pinned before preflight. The native helper uses that authenticated
hash and independently checks the actual published envelope and every release
asset before opening; it does not implement another signature algorithm.

Image ancestry and all current image support-file hashes are captured dynamically.
The immutable manifest still pins the reviewed five-binary source baseline.
No cache ABI or SQL migration is introduced by this release.

Activation errors restore the prior image and reopen only if the old paired
public channel and all preserved-state checks still pass. A new/unknown channel,
persisted data drift, or failed recovery holds the gateway closed. Failed `open`
validation restores the old image but holds access for pairing reconciliation.
If gateway opening might have succeeded, recovery closes access, retains the
candidate image and all subsequent player activity, and forbids replay. **No
recovery path restores SQL, old inventory, receipts, or saved player positions.**
Do not delete evidence to rerun an uncertain operation; reconcile the recorded
state and use a separately reviewed recovery action.

Offline validation: `python docs/tradeskills/deployment/native/test_rollout.py`.

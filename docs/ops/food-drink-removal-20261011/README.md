# Food and drink requirements removed — October 11, 2026

The owner explicitly approved main promotion and OVH deployment. PR #162 is
merged and live. Every zone reports full food/water meters and no starvation;
nutrition consume requests preserve inventory. Player access is open.
Client warning rendering and the [exact in-game QA](../../qa/2026-10-11-food-drink-removal.md)
remain owner acceptance. No client update is required.

## Release and verification

- [PR #162](https://github.com/frank-grimes-jr/nightcap/pull/162), main merge
  `d05886fa84279ee3c10e90d4db9afe4bd7fb8cda`.
- Follow-up verified at `2026-10-11T23:31:51.524358+00:00` (October 11 in America/New_York).
- New immutable image: `sha256:a72aa7931198ec96f67f69432ecccabc78640ce20de75d3da6f23e647c5be903`.
- Zone SHA-256: `989e64c181b002a4f34562af71389ed3b54a93ce707856cb85e9a19cab0fcf03`.
- Deployment package SHA-256: `521a7151f0118ea341ed1467963318745940d0ef9915250345724fbf9c39348d`.
- 250 compiled nutrition checks plus the login ordering guard; 99 heal-targeting
  checks; eight rollout/recovery/GM-maintenance tests. A fresh complete zone build
  passed against fingerprinted retained live source. All nine changed C++ method
  bodies remained identical after rebasing onto current main; tests passed again.

Preflight verified the exact deployed baseline, image ancestry and native/crypto
contracts for both images, then took a verified full PEQ backup. Activation held
both the deployment lock and the GM maintenance lock, rejected active GM
maintenance/in-flight SQL, closed access and stopped the supervised game cleanly.
No individual zone was killed. After startup, all 12 zone process hashes matched.

Before reopening access, checks preserved 47 player/state tables,
9 custom tables, all rules and content checksums. The unchanged world
still owns market rotation; its two rotating market tables are excluded from
static custom-table checks. No SQL restore or migration ran. Other native binaries,
quest/plugin fingerprints, published channel/guide fingerprints and DB/web/tunnel
containers were preserved. The existing credential gateway reopened successfully.

Post-activation and follow-up checks report zero new-runtime restarts and zero
detected native/quest/database errors. The previous container had one historical
restart at preflight; it is retained as baseline history, not attributed to this
release. [Evidence](deployment-evidence.json) includes the verified backup metadata,
activation counts and actual process hashes, without exporting player rows.

## Behavior and balance

HP/mana/endurance regeneration now always uses the ordinary fed behavior; there
is no hunger/thirst penalty, regardless of old rules or saved meter values.
Login initializes both meters before the client profile, and periodic stamina
updates and quest setters keep them full. Manual/automatic consume requests no
longer delete food/drink inventory. Optional edible bonuses, recipes, quests and
alcohol behavior remain. Stat food no longer has an upkeep cost; no additional
stats, regeneration bonuses or higher caps were introduced.

## Retained artifacts and recovery

Local package/build evidence: `E:/EQ_Local_Dev/artifacts/remove-food-drink/`.
OVH release: `/opt/nightcap/releases/food-drink-removal-20261011/`.
The remote directory retains the verified package contents, `rollout.py`, private
full backup and preflight/stopped/activated evidence. Its build manifest records
the original build-source commit; the main merge and exact-method comparison
record the rebased source promotion. The earlier local build-only archive remains
a dated build artifact; [package.json](package.json) identifies the deployed bundle.

Rollback image: `sha256:0c8939425172b588af1c30ac9a1a4df0f193992bee80809e52e5c748f5ad069c`.
Prior zone SHA-256: `a3d23a90f7108f9bc030943669d809f04dd7542fc3a0a18af56cd02a8061a412`.
Automatic activation recovery selects that exact receipt-aware image while
retaining all current character, corpse and receipt data. No database restore.

For subsequent operator recovery, acquire `/opt/nightcap/deploy/production/.deployment.lock`
and `/var/lock/nightcap-gm.lock`, reject existing GM maintenance or in-flight GM SQL,
and confirm the current image still matches this release. Stop gateway and game
gracefully, use the rollout's atomic `select` operation with the recorded old image,
start game through the Compose health gate, verify the recorded baseline process
hashes and open gateway only after those checks. Retain current SQL state; an old
database or pre-receipt image is never a valid rollback. Restoring this old image
also restores its old food/drink behavior.

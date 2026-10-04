# Winged Paladin helmet: live deployment

October 4, 2026. Deployed for owner testing, with native visual/equip acceptance
still open. The owner explicitly requested: "I want to do this on the server.
Push to main and the server." This superseded the isolated-client QA gate.

Source feature and authorization were pushed to main at e250828. Production
game release **2026100401** is public at play.nightcapgame.org; the existing
launcher downloads the update before Play. No new desktop launcher is needed.

## Delivered

- Editable Blender source, Unity FBX inspection and native HE90 variants for
  both genders of all twelve original races. Later races are excluded.
- Item **990500 — Winged Helm of the Dawn**: Paladin only, original races,
  head slot, AC 18, HP 25, mana 25, STA 5, WIS 7, MR 10, FR 5, CR 5, weight 4.5,
  magic/no trade, no effects, heroic stats or augment slots.
- Camil Swiftwolf, NPC 999521 in East Commonlands, now uses helmtexture 90.
  Only that NPC field changed. His body/face, tint, weapons, location and one
  non-corpse instance-0 saved-state row were preserved. His loot table stays 0.
- No quest, merchant or loot acquisition source was introduced.

## Verification

All 48 public release files were downloaded over HTTPS and checked against the
production signature using the public key shipped in launcher 0.3.1. Total:
160,550,091 bytes. All 46 previous files are unchanged; global_chr.s3d and
global4_chr.s3d are the only additions. The desktop channel, starter ZIP and
guide remain unchanged. See [hosted verification](hosted-verification.json)
and [publication receipt](published.json).

Camil's operation took a fresh full database backup while game processes were
stopped, captured his current content/cache rows, rehearsed the guarded update
with rollback, then applied and compared the exact afterimage. No cache row
was deleted. World and all 12 zones restarted; native binary hashes are
unchanged and the helmet is present in shared/items. Game/DB health passed;
gateway, web and tunnel are running. See [deployment receipt](camil-deployment.json)
and [final service/public state](production-after.json).

Thirteen helmet/item tests, five gameplay-generator tests, three PFS tests and
the Go package suite pass. Fresh canonical asset generation reproduced all 44
gameplay files exactly. Independent code review resolved its missing helmet
integration. Focused operation review resolved recovery-gate and backup-timeout
issues before execution. These checks do not prove native rendered appearance.

## Live QA

1. Close the game and start the normal Nightcap launcher. Confirm game release
   2026100401, then enter East Commonlands and inspect Camil at the tunnel class
   area. His helmet should have a silver shell, gold face edging and tall pale
   feathered wings; his existing outfit, weapons and location should be intact.
2. On a GM character with Paladin available, preserve the existing head item,
   use `#summonitem 990500`, and equip the new helm. Check its listed stats and
   front/side/rear appearance, head animation, removal/re-equipping, zoning and
   reconnect. Compare the ordinary helmet afterward.
3. Verify all 24 original race/gender fits, secondary/tertiary Paladin eligibility,
   rejection without Paladin, and crowded-zone performance. Modern-model opt-in
   is not validated. All these native checks remain pending.

Full scope and visual references: [helmet guide](../../helmets/winged-paladin.md).

## Recovery and retained evidence

Fresh pre-Camil full backup:
`/opt/nightcap/backups/winged-helmet-20261004/camil-live/peq-before.sql.gz`.
SHA256: `14f910dc73b67a2c6fd0caa1f6fd57facbea39baebb88e16d7e4b2b117e3d5a0`.
Gzip validation read 444,490,733 uncompressed bytes. Scoped before/after JSON,
SQL and the deployment receipt are retained alongside it.

For an appearance rollback, capture fresh stopped-server Camil/cache state and
use [the guarded head-only rollback](camil-rollback.sql) only if its full NPC
afterimage still matches. Retain unrelated state and any new player-owned item
instances. Do not run the old item-deletion rollback after player distribution.

Client recovery requires publishing the previous reviewed archive bytes as a
**higher game release**; do not move the public channel backward after clients
have observed 2026100401. The prior channel is retained at
`/opt/nightcap/releases/winged-helmet-2026100401/previous-channel.json`.

The Python/SQL files here archive the exact operation source. They depend on
the original private evidence directory
`E:/EQ_Local_Dev/artifacts/winged-helmet-20261004/`; they are not a general replay
command. Recapture state and review a new operation for any follow-up. The
prepared publication-diff JSON records the pre-publication comparison; the
publication/deployment receipts establish the completed state.

# Tunnel class courts: production deployment

Deployed September 30, 2026 to `play.nightcapgame.org` after the owner approved:
"Approved. push to main and to the server". [PR 94](https://github.com/frank-grimes-jr/nightcap/pull/94)
merged as `453e61bf150fcabc75ef34ef8ada199c2f15fd15`. This is live-QA authorization;
manual visual and interaction acceptance remains open.

## Live content

Sixteen trainer/shop pairs occupy eight courts with matching class race, armor
and colors. Twenty-two suppliers use profession outfits; fourteen spillover
subtitles use Roman I–IV. Stock links, prices, trainer functions and progression
remain unchanged. Bartholomew uses a familiar Halfling model.

Khalure has **Druid Rings** at `/loc -1561,-311,3.75`. Khaleid is a male Dark Elf
with **Wizard Spires**, Classic Carmine Robe material 15 and Blue Crystal Staff
model 122 at `/loc -1567,-279,3.75`. His eight Classic destinations and travel
guards are installed. Uniforms and native subtitles provide identification;
no custom wall-sign asset or client update was needed for this content release.

## Verification

- Fresh stopped-target capture; full PEQ backup (444,032,895 uncompressed bytes)
  restored and verified in an isolated, network-free MariaDB container.
- All 19 migration/recovery checks and exact forward/rollback rehearsals passed.
  Only affected instance-zero, non-corpse NPC saved states were invalidated.
- All 50 preservation fingerprints matched, including player data, advanced-loot
  claims/preferences, rules, stable merchant stock and unrelated saved states.
- All scoped static afterimages match. Runtime files are installed in active
  `plugins/` and `quests/ecommons/`; existing quest/plugin/Lua files match baseline.
- All nine current map hashes and zone metadata were pinned. Fresh native probes
  passed 550 court ground/headroom samples, 55 approach rays and 40 landing samples.
- All 26 quest assertions passed using the installed files inside the game
  container; three Perl syntax checks passed. These use mocked client/NPC APIs,
  so they do not claim a rendered or authenticated in-game interaction.
- All 15 native process hashes match the retained advanced-loot image
  `sha256:c02b2b3ceb1e64ea99226384cd22a6d51c8e9da82b264580f41b0cc901de7d5f`.
  Game start: `2026-09-30T23:54:32.404571423Z`; zero unexpected restarts or matched
  quest/native/database errors. Existing startup policy advanced market epoch
  12 → 13 with the expected 20 sell, 12 buy and 10 find offers.
- Gateway reopened after verification; public TLS/native session handshakes
  passed for login 5998, world 9000, chat 7778 and zone 7000.
- Twenty-one isolated orchestration fault tests and independent review passed.

The original verification step hit Docker's read-only-rootfs restriction when
copying its public test fixture. Access stayed closed. The reviewed
`verify_open.py` continuation delivered that fixture through exec into tmpfs,
repeated preservation/health/content checks, and opened access after they passed.
SQL and installation were not repeated. [Archived operations](ops/README.md).

[Sanitized evidence](PRODUCTION.json) includes exact backup/package hashes and
live porter definitions. Full private backup/preimages remain on OVH under
`/opt/nightcap/releases/tunnel-courts-evidence-20260930/`.
The pinned package is `/opt/nightcap/releases/tunnel-courts-20260930/`.

## Recovery and acceptance

For authorized scoped recovery, use the pinned helper under the deployment lock:

```sh
sudo -n flock -n /opt/nightcap/deploy/production/.deployment.lock python3 /opt/nightcap/releases/tunnel-courts-20260930/rollout.py rollback
```

This closes access, stops writers, captures current preservation, validates
static afterimages and fresh NPC references, restores original content and
removes only the three matching added scripts. It retains the receipt-aware
advanced-loot image and current player/claim data. Ambiguous corpse/other-instance
references or static drift stop recovery. Never restore the full backup over
later player progress or switch to an older receipt-unaware server.

Run the [exact owner QA](README.md#exact-owner-in-game-qa), particularly outfit
rendering, label readability, all trainer/merchant interactions, both porters,
all eight wizard landings, and persistence. Record screenshots and `/loc` for
presentation issues. Automated checks do not establish manual acceptance.

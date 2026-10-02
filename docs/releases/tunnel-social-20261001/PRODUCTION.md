# Social tunnel deployment - October 2, 2026

The approved social revision is live on OVH. Source `9a353d3` reached main in
[PR 111](https://github.com/frank-grimes-jr/nightcap/pull/111), merge `386854d`.
The dev/test promotions are PRs 109 and 110. The scoped main promotion excludes
the unrelated Epic campaign waiting on test and retains the current client UI
repairs. Rendered owner acceptance remains open in the [exact QA](README.md#exact-in-game-qa).

All 119 audited actors remain present. The release updates 16 class merchant
names, 93 spawn poses, eight pause modes, 32 waypoints and six crafting-station
poses. It installs seven quest/plugin files. The six named residents occupy an
uneven gathering, class counterparts meet in eight small groups, traders remain
dispersed, the Chronicler stands by Shady, and supplies surround the southwest
crafting stations. Existing uniforms, Roman supply pages and porter services
remain intact.

Useful East Commonlands locations, in `/loc` order Y, X, Z:

- Tradeskill corner: approximately `-1780, -330, 3.75`.
- Sortre, Camil, Rekk, Nalin, Trift and Glorphyndel: around `-1707, -274, 3.75`.
- Chronicler: `-1702, -141, 3.75`; Shady remains at `-1677, -141`.

## Verified production evidence

[Machine-readable evidence](production.json) records the activation and the
fresh stopped-server rehearsal. No character records or private backup contents
are published.

- A 444,493,359-byte uncompressed full database backup restored in an isolated
  database. All 17 regression checks and exact full-database forward/rollback
  comparisons passed.
- All 59 table/scope preservation fingerprints matched before reopening:
  player data, inventory, currency, rules, merchant stock and unaffected content.
- All 93 relocated-actor cache rows were invalidated; all four scoped unchanged
  native cache rows remained. No NPC definitions or spawn rows were deleted.
- All 72 assertions passed against the actual installed social, resident and
  wizard quest files. All seven changed files passed Perl syntax checks.
- All 15 native processes match the previously deployed image hashes. The image
  remains `nightcap-game:advanced-loot-20260930`; no binaries or client assets
  changed. Only game was recreated, with dependency recreation disabled.
- The game is healthy with zero activation restarts and no detected quest API,
  native-crash or database errors. The normal startup advanced market epoch
  14 to 15 and retained expected offer counts: 10 find, 20 sell and 12 buy.
- Public TLS and native handshakes passed for login, world, chat and zone ports
  5998, 9000, 7778 and 7000 before final activation was recorded.

The existing live resident scripts used CRLF endings. Their contents matched
the Git preimages exactly after newline normalization; the release pinned and
backed up their original byte hashes for exact restoration.

## Recovery and remaining acceptance

Private backup, runtime preimages and generated SQL remain on the server under
`/opt/nightcap/releases/tunnel-social-evidence-20261001`. The pinned helper is
`/opt/nightcap/releases/tunnel-social-20261001/rollout.py`. Run recovery under the
production `.deployment.lock`, with access closed and a fresh content capture.
Rollback restores only scoped content and the seven affected runtime paths,
preserving subsequent play and invalidating fresh relocated-actor caches.
Never restore the old full database over newer player progress.

Native terrain checks and the placement diagram do not prove client rendering.
The owner still needs to inspect group spacing, uniforms, animated social
behavior, every merchant page, station interaction, and walking routes using
the linked eight-step QA. No wall textures or client asset changes were needed.

# Interactive Nightcap handbook — October 22, 2026

The owner requested a modern, fun, interactive HTML wiki. The implementation
keeps the static generator, all 458 routes, existing artwork, gameplay prose,
release labels, 384 reward values and existing equipment filters. It adds four
home reading paths, quick search, local bookmarks, two reading themes, mobile
navigation, reading progress and a desktop contents rail. Home release notices
are moved intact below the discovery tools, with deep-link expansion.

## Design and acceptance

The affected files are `wiki/build.py`, `experience.py`, the two `experience`
assets, tests, About and Recent changes. The sequence was shared shell/home,
browser enhancements, accessibility/responsive checks, then publication evidence.
The main risks are losing current guide content, breaking generated routes or
publishing over another editor. Preserve the public asset allowlist and compare
the origin manifest against a reproduction of the starting source before update.

A framework migration would add dependencies without improving this public
read-only guide. A cosmetic restyle would leave discovery and long release-note
stacks unresolved. Progressive HTML with small browser enhancements meets both
needs and preserves no-JavaScript reading.

Acceptance: all existing links/anchors and catalog values pass; search handles
commands, exact items, empty/unsafe input and request failure; saved pages survive
reload and handle blocked storage; path URLs restore through Back; layouts have
no horizontal overflow at 320/768/1024/1440; keyboard dialogs close and restore
focus. No game/client/cache/SQL changes or new external services are involved.

## Verification and whole-wiki review

`verification.json` records automated and browser checks. `wiki-review.json`
records all 21 maintained guides, 432 generated item/zone routes and the source
drift review against main c6c2100. About explains local preferences and shortcuts;
Recent changes announces the interface. Gameplay Features, commands, catalog and
candidate labels retain their meaning. Home notices remain byte-identical within
the new presentation. Publication does not change native gameplay acceptance.

Initial Windows sandbox test attempts could not access their temporary package
and Git fixtures. The unrestricted rerun passed; the Linux-only publication and
recovery checks run on the host before the pointer change.

## Publication and recovery

Published as **20261022-interactive-handbook-v1** at
https://wiki.nightcapgame.org/. Both `wiki-publication.json` and
`wiki-public-verification.json` report PASS: all 465 hashes/security headers,
five private-route denials, 16 Linux recovery tests and actual pointer rollback.
The public browser also renders the new home and quick search without errors. `publish.py` uses the unchanged
guarded updater, asserts the expected prior release and its complete manifest,
runs Linux recovery tests and rehearses the old/new pointer. The current source
and package must match the recorded file hashes. Only public wiki files change;
services, Nginx, private downloads and player access remain unchanged.

Recovery uses the updater's exact previous pointer/config receipts in the shared
website-history directory. Hold its lock and verify current ownership before
restoring the previous immutable relative pointer. Never overwrite a subsequent
publisher's release. See `docs/ops/nightcap-wiki.md`.

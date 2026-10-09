# Pet window layout repair: release 2026100104

Published to OVH following the owner's explicit main/live approval. The release
changes only `uifiles/nightcap/equi_petinfowindow.xml` among 46 managed assets.

## Cause and correction

The compact generator changed the native buff panel's Location/Size but retained
stock AutoStretch anchors. RoF2 uses those anchors, placing buffs over the roster,
health gauges and command buttons. Set the effective anchors to left 180, top 122,
right 6, bottom 4. Buffs now occupy the area below the roster and beside commands,
expanding with the window. Default/minimum size remains 350 x 350. Move the
clear-target hint into the All pets tooltip to free the growing buff area.

All 85 native buff controls and advanced-loot definitions are preserved. Command
behavior, other client assets and character INIs are unchanged.

## Evidence and operational limits

- The regression fixture reproduces native AutoStretch anchors. Its effective
  rectangle checks failed before the fix at all four sizes; the three pet UI and
  four gameplay UI checks subsequently passed. Twelve publisher recovery checks
  passed. Independent review found no blocking issues.
- Generated previous XML matched the installed release 2026100103 exactly.
  Only the buff panel, All pets tooltip, removed hint and screen reference changed.
- Publisher verified all 46 hosted assets and published the signed channel last.
  All five service identities, start times, restart counts and health states were
  preserved; the game already had restart count 1 before this publication.
- Desktop launcher, starter download and guide are preserved. No server restart
  or database write was needed.
- Public HTTPS channel and pet XML match the signed candidate byte for byte.
- Evidence: `artifacts/pet-window-repair-20261001/` (local ignored directory).
  Channel SHA-256: `f7ecc3dab1c9931b916dbbbe14430726cc6b13f00152d423a581353f35d88f78`.
  Pet XML SHA-256: `8796b93a63679847e0ac5b4faa78f1a807b3cecb13480ea8e040b1db7f6d7fd6`.

File/signature checks do not establish rendered in-game acceptance. That remains
pending. Close the game, open the normal Nightcap launcher and click Play to apply
the patch. The launcher preserves existing saved window dimensions; resize the
pet window down to its minimum if an older large size is restored.

## Owner QA

In East Commonlands, open Pet Info with one pet, then with all three class pets.
Check roster rows, scope, health gauges and every command remain unobscured.
Apply pet buffs and confirm icons/tooltips appear below the roster, to the right
of commands. Resize to minimum, enlarge, close/reopen and reload the UI. Buffs
must stay within their panel, and selecting a pet / All pets must still select
the displayed command scope. Full lifecycle steps remain in
[pet-management QA](pet-management-20260922/QA.md).

## Recovery

The previous channel is retained on the host at
`/opt/nightcap/releases/pet-window-2026100104/previous-channel.json` and release
2026100103 remains immutable. For clients that have already accepted 2026100104,
publish restored XML in a newly signed higher release number, preserving current
other assets. Do not lower the release counter or change production trust keys.

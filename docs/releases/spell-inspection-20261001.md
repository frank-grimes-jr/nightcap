# Spell inspection class audit — October 1, 2026

Verified implementation and signed local QA candidate; not published. The owner reported
unusable classes with level 255 in the in-game inspection window.

## Accepted behavior and scope

Both native scroll-detail builders must list only the canonical original spell
classes, with each class's own original level. A character's lowest held-class
level must not replace an original class's displayed level. Preserve native
zero masks, non-scroll inspection, merchant filtering, scribing, memorization,
casting and server authorization. Unknown spell eligibility fails closed.
No database/class-catalog rewrite or original-client modification is required.

Implemented display-only mask and level redirects in `ui_hooks.h`/`dllmain.cpp`
and bound all four exact call sites into the shared signed catalog. The x86
reproduction, complete native runtime suite, full launcher suite and isolated
signed installation pass. Rendered owner QA remains open before publication.
The main risk is accidentally applying the character's primary-class projection
to an original-class label. Keep that projection confined to existing access
queries. Regression tests must cover shared spells, unknown spells, stale or
missing character identity, native rejection and all canonical class rows.

## Read-only audit

The installed `E:/Nightcap/spells_us.txt` contains **40,723 spells** and
**651,568 class-level fields**. All class fields match the pinned original
catalog; the independently generated Ancient Attunement (42604) is preserved.
Original catalog SHA256:
`bae7ba7d897962f67581e3e731b94f4a31898d160c30c2edb74912b21aa11880`.
Installed spell file SHA256:
`56915e0e489422a7befb1f3255610a8f6c1cb2163252aa05476a6dfea4270456`.

A read-only consistent snapshot of all **11,719** hosted `itemtype=20` rows
found **10,476** with a packaged spell. Of these, **7,636** have **18,990** extra
class bits whose canonical spell level is 255. No legitimate class bits need
adding. No captured scroll with a packaged spell uses a 253/254 level marker;
those original AA-related catalog markers retain their existing semantics.
The other 1,243 rows include non-spell recipes/instructions and spell IDs absent
from this client; they are separately inventoried, not claimed as rendered bugs.

Examples: Tunare's Renewal (spell 2179, item 2482) has item mask 292 but canonical
Druid-only mask 32; Kragg's Mending (2435, item 2483) has mask 516 but Shaman-only
mask 512. The old renderer blindly prints a level for every item-mask class.

Evidence: `E:/EQ_Local_Dev/artifacts/spell-inspection-20261001/scrolls.json`
and `audit.json`. Reproduce with `tools/audit_spell_inspection.py --spells ...
--original ... --scrolls ... --output ...`. This tool reads inputs only and
rejects packaged class drift or duplicate item identities.

## Exact native evidence

Supported executable SHA256:
`2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e`.
Both class-list builders test the scroll item mask, then unconditionally format
`%s(%d) ` using the spell-level accessor. There is no unusable-level filter.

| RVA | Original bytes | Call |
| --- | --- | --- |
| `0x2A39CE` | `e80d131100` | First detail path: item class mask |
| `0x2A39E0` | `e81bbde0ff` | First detail path: original class level |
| `0x2A6D11` | `e8cadf1000` | Second detail path: item class mask |
| `0x2A6D21` | `e8da89e0ff` | Second detail path: original class level |

The separate spell-window character-level query already rejects levels >=254.
Changing every spell-level query or replacing 255 in spell data would alter
access semantics and fail to address the wrong item-mask enumeration.

## Verification and staged delivery

- Independent x86 reproduction executes the two exact native enumeration blocks
  with their bit tests, loops, formatting and concatenation intact. Before the
  fix, both show `WAR(255)` and false `CLR(17)` for Summon Waterstone. After the
  fix, both show only `MAG(17)`; Courage retains `CLR(1) PAL(15)` even when the
  character can use it at level 1. Read-only byte comparison matches both test
  blocks to the pinned original executable.
- The new hooks pass all **15,670 catalog spells / 250,720 class levels**, plus
  native zero, non-scroll, unknown IDs, invalid pointers, stale/no identity and
  existing 253/254 semantics. Existing access/merchant/scribing tests pass.
- The x86 DLL and runtime test binaries build; all five Python runtime checks
  pass. Four spell catalog/audit tests and five asset tests pass. The complete
  Go launcher suite passes outside the sandbox (its directory-lock tests cannot
  access user-directory ancestors inside the sandbox).
- Independent production-hook review found no required changes: exact call
  bytes/ABIs, required startup failure, identity independence and access scope
  were checked. No game client was launched for these synthetic checks.
- Signed local QA **2026100102**, proxy **0.7.1-dev**, verifies **67 patch sites**
  and installs **46 managed files** through the real launcher controller into
  `artifacts/spell-inspection-20261001/install-check`. This is an installation
  fixture, not a complete playable client. The existing game helper and all 42
  gameplay assets retain their hosted 2026100101 contents. Only the proxy and
  patch catalog differ. No live client, hosted channel or database was changed.

The locally signed bundle is under this worktree's
`eq-launcher/internal/launcher/qabundle`; the QA controller is
`E:/EQ_Local_Dev/artifacts/spell-inspection-20261001/nightcap-qa-check.exe`.
It uses an isolated QA key, not production trust. Publishing through the usual
launcher requires main/live approval and signing under the existing production
key. Before publication, recheck the live channel and select a higher counter
if another release has used 2026100102. Preserve the 42 gameplay assets and helper.
If recovery is necessary after clients update, publish a higher-numbered
corrective release; do not lower the channel or change player/server state.

## Exact owner QA (required before main promotion)

1. Use the isolated signed candidate client, enter East Commonlands, and inspect
   Summon Waterstone at a Magician spell merchant or from a scroll/link. Its
   original list must say **Magician (17)** only, regardless of held classes.
2. Inspect Light Healing: **Cleric (4), Paladin (12), Ranger (21), Druid (9),
   Shaman (9), Beastlord (20)** only. A Cleric/Paladin character must still see
   Paladin 12 in that list, even though its own usable level is 4.
3. Check both a merchant scroll inspection and an inventory/chat-link inspection
   of the same spell. No original class may show 255. On a QA character with
   other classes, the original list remains the same.
4. Confirm the usable-only merchant filter and scribing a held-class scroll
   still work. An unheld spell and an above-level held spell stay restricted.
   Check an ordinary weapon/armor inspection retains its original class list.
5. Zone and relog, then repeat inspection. Record the candidate release and
   fresh proxy log. Database writes, character respecs and gameplay promotion
   are not prerequisites for this display-only verification.

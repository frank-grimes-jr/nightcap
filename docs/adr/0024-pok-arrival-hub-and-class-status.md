# ADR 0024: PoK arrival hub and explicit class status

Date: 2026-09-13. Status: selected by the owner; implementation in progress.

## Decision

Create one compact service hub near PoK arrival with a class guide and clearly
labeled class spell/discipline merchants. The owner selected this layout over
reorganizing the existing location. Work is isolated on feature/pok-usability,
based on dev, without changing the AA ownership branch or deploying its binary.

Use the existing server quest interface for the short-term class experience.
Show Primary, Second, and Third slots explicitly, including Not selected. Show
status on hail, at login, through #classes or /say !classes, and immediately
after the existing class plugin handles a selection or release response.
Keep confirmation before selection. Describe access and earned skill progression
accurately rather than showing counts derived from globally widened spell data.
A custom permanent character-panel display is a separate client feature.

Keep the canonical character_multiclass record and native gameplay mechanics.
This UI increment does not implement AA refund, grant, or class-release mechanics.
Do not mix the in-progress AA binary into the usability release.

## Merchant data

The current restock uses globally widened spells_new class columns, so class
labels do not reliably describe stock. Martial Loremaster is labeled Melee Tomes
but has 120 Spell entries, 63 Song entries, and no Tome entries by item name.
The existing overflow vendors use vague II/cont. labels.

The original downloaded spells_us.txt and untouched server export have the same
SHA256: bae7ba7d897962f67581e3e731b94f4a31898d160c30c2edb74912b21aa11880.
The read-only audit in ../pok/hub-stock-audit.json matches all 1,229 currently
stocked unique scrolls by spell ID and name against this source. Every scroll has
an original class eligible by level 50. Per-class stock ranges from 3 to 275,
below the 500-item RoF2 merchant limit, so one merchant per class fits today.

Preserve the existing available item set and prices while organizing stock by
original class eligibility. Do not use the widened spell/item masks as the
classification source. Keep the downloaded client data read-only. Placement,
guarded reversible SQL, restock integration, and in-game QA remain to implement.

## Verification and remaining gates

Lua behavior tests cover every primary class, empty slots, command handling,
login status, and delegation of other commands. Sixteen Perl dialogue assertions
cover hail/preview without mutation, confirmation opening, selection response,
failed selection display, and slot promotion after release. The existing canonical
login-banner regression passes. These use mocked client/plugin interfaces and do
not replace in-game QA or prove the native class mutation paths are complete.

Before promotion, provide exact QA steps for normal-player status commands,
Yes/No selection responses, immediate status, relog, labels, merchant contents,
prices, ground placement, and unobstructed arrival paths. NPC/merchant changes
need a PoK restart; scheduling that activation remains with the owner while playing.

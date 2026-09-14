# GitHub issue review — 2026-09-14

## Scope and evidence boundary

Reviewed all 24 open issues and open PRs (none) through the GitHub API. Published main was `191bf8e`; dev `0d3bb96`; test `477852c`. The local main `f7943c1` is 121 commits ahead and includes candidate work whose own documentation still requires QA. This review does not synchronize or promote that branch. Docker Desktop's Linux engine was unavailable; no fresh database or in-game results are claimed.

The owner authorized closure of the six resolved issues below after publication. Existing recorded acceptance is used; today's checks verify repository ancestry and the accepted DLL's exact client signatures, not a new play session.

## Resolved issues

| Issue | Published implementation / evidence | Disposition |
|---|---|---|
| [#8 Heroic stats](https://github.com/frank-grimes-jr/nightcap/issues/8) | [f5422b4](https://github.com/frank-grimes-jr/nightcap/commit/f5422b4): Ascended heroics and 425 base stat cap; heroics may raise totals above 425. | Close as completed after publication. |
| [#9 Duplicate spells](https://github.com/frank-grimes-jr/nightcap/issues/9) | [a3f6194](https://github.com/frank-grimes-jr/nightcap/commit/a3f6194): One scroll per spell; docs/qa/2026-07-15-qa-spike.md records zero duplicates. | Close as completed after publication. |
| [#21 Spell vendor cap](https://github.com/frank-grimes-jr/nightcap/issues/21) | [590d7d8](https://github.com/frank-grimes-jr/nightcap/commit/590d7d8): Split vendors: Arcane 388/388, Divine 344/343, Stalwart 341/340, Martial 184; all below RoF2's 500 cap. | Close as completed after publication. |
| [#25 Item scaling](https://github.com/frank-grimes-jr/nightcap/issues/25) | [870fdd0](https://github.com/frank-grimes-jr/nightcap/commit/870fdd0): Necklace 9289 THJ reference calibrated family scaling; later balance work remains separate. | Close as completed after publication. |
| [#24 Stat reference](https://github.com/frank-grimes-jr/nightcap/issues/24) | [f5422b4](https://github.com/frank-grimes-jr/nightcap/commit/f5422b4): Consumed design reference in #8/#25; not a claim of complete THJ/endgame balance. | Close as completed after publication. |
| [#12 DLL proof/proxy](https://github.com/frank-grimes-jr/nightcap/issues/12) | [397d51b](https://github.com/frank-grimes-jr/nightcap/commit/397d51ba7626018a2574bc29ac4e54392306805b): B0/B1 and caster UI/mana evidence; July 28 sign-off in docs/qa/2026-07-28-mana-gauge-test-qa.md. Exact-client B2 checks passed again September 14. | Close as completed after publication. |

The DLL acceptance commit is published as `feature/accepted-mana-gauge`; its historical README's “QA pending” line is superseded by the dated July 28 sign-off. #12 closes only its original proof/proxy scope. #10, #13–15, #36, #38 and #39 retain broader capability and delivery requirements.

## Issues that remain open

| Issue | Status | Next step / closure gate |
|---|---|---|
| [#4](https://github.com/frank-grimes-jr/nightcap/issues/4) | Decision required | AA prefixes are a workaround, not the requested AA-window column. Choose whether labels suffice or schedule an exact-build DLL column implementation. |
| [#10](https://github.com/frank-grimes-jr/nightcap/issues/10) | Partial; release gates open | Server and held-Monk slices exist locally. Require complete class/slot acceptance, remaining client UI and equipment support, AA lifecycle recovery, launcher delivery, and final in-game sign-off. |
| [#11](https://github.com/frank-grimes-jr/nightcap/issues/11) | Partial; acceptance gaps | The original mana/HP implementation is published (23fd3f3), but its changelog defers AC/stat-cap best-of and heroic INT/WIS regen, and records smoke tests rather than the full WAR/NEC acceptance. Confirm remaining A2 scope and capture best-of stats in game before closing. |
| [#13](https://github.com/frank-grimes-jr/nightcap/issues/13) | Partial; client parity open | Accepted caster UI/mana work does not certify off-base equipment or full held-class parity. Validate truthful WAR/NEC scribe/memorize/cast, NEC-only equip, negative restrictions, and /who. |
| [#14](https://github.com/frank-grimes-jr/nightcap/issues/14) | Not delivered | Implement the signed whole-generation client manifest and branded launcher specified by #10; validate clean install and later update. |
| [#15](https://github.com/frank-grimes-jr/nightcap/issues/15) | Not delivered | Complete per-feature DLL hardening, signed launcher/release pipeline, interruption/rollback and unsupported-client tests, then clean-install QA. |
| [#16](https://github.com/frank-grimes-jr/nightcap/issues/16) | Started: read-only audit | New title/ownership audit and 10 tests identify exact missing type-1 titles across rank chains. Live snapshot is blocked by stopped Docker; no disablement applied. Run the preflight, resolve saved ownership, back up, then implement reversible disablement and zone/UI QA. |
| [#17](https://github.com/frank-grimes-jr/nightcap/issues/17) | Partial candidate | PoK native-class merchant routing candidate improves stocking; global tooltip widening and per-character client spell access remain. Keep candidate separate until reviewed and QA passes. |
| [#19](https://github.com/frank-grimes-jr/nightcap/issues/19) | Investigated; unverified | Capture standing/running Selo's speed, buff state and instrument modifier for both variants, with Bard-base and held-Bard controls. Data/math inspection alone did not prove a fix. |
| [#20](https://github.com/frank-grimes-jr/nightcap/issues/20) | Unfixed | Reproduce song landing while running versus standing, with interrupts and held-Bard/base-Bard controls. Diagnose packet/cast completion before changing the permanent-song system. |
| [#22](https://github.com/frank-grimes-jr/nightcap/issues/22) | Not implemented | Inventory the bag merchant's exact item IDs, slots, capacity and current buy/sell values. Propose a price ladder against vendor income and #sellall; require transaction/round-trip and in-game merchant QA. |
| [#23](https://github.com/frank-grimes-jr/nightcap/issues/23) | Undeployed | index.html is already published in main (dd44e3a), but GET /repos/frank-grimes-jr/nightcap/pages returns HTTP 404 on 2026-09-14. Review player claims against shipped features, enable Pages and verify the live tabs/site before closing. |
| [#26](https://github.com/frank-grimes-jr/nightcap/issues/26) | Design only | The zone-augment design is recorded. Build a zone/era/content manifest, collision checks, balance fixtures and reversible SQL; no augment deployment is established. |
| [#32](https://github.com/frank-grimes-jr/nightcap/issues/32) | Reverted from published main | The waypoint implementation was reverted by 6b44430/789e410; later local proximity work is not a published-main release. Reconcile scope and Lua precedence, then test discovery, recall, persistence and Explorer title before promotion. |
| [#36](https://github.com/frank-grimes-jr/nightcap/issues/36) | Partial; client gate | Server skill eligibility/seeding work exists, including later value-1 lifecycle policy. RoF2 Skills/client coverage and full class/slot QA remain; auto-grants alone do not close the report. |
| [#37](https://github.com/frank-grimes-jr/nightcap/issues/37) | Partial; runtime QA pending | Character:AAExpMinLevel was repaired to 1 locally and #aaexp exists. Verify active world/zone rules after a controlled reload/start and prove XP split/gain/persistence at level 1 in game. |
| [#38](https://github.com/frank-grimes-jr/nightcap/issues/38) | Partial; client equip blocked | Server held-class equipment checks are improved, with later weapon-damage candidate work. RoF2 still blocks off-base equip attempts. Validate client submission plus server race/deity/slot/level and non-held-class rejection. |
| [#39](https://github.com/frank-grimes-jr/nightcap/issues/39) | Partial; client trainer blocked | Mask-aware server trainers and skill auto-grants do not prove RoF2 trainer interaction. Test held trainers, non-held refusal, unlock thresholds, points and skill caps in game. |

## Work begun and verification

- #16: [audit runbook](../ops/aa-client-title-audit.md), read-only SQL snapshot and Python report. Ten unit/CLI tests pass, including rejecting truncated ownership exports and input overwrite. Actual local RoF2 dbstr parsing found 2,470 nonempty type-1 title IDs; this is not a count of broken AAs.
- The initial test run failed because the implementation module did not exist; after implementation, all ten tests passed. No tests disabled.
- Accepted DLL checkout `397d51b`: `eq-client-dll/tests/verify-exact-client-patch-sites.ps1 -EqgamePath <local eqgame.exe>` passed exact file hash/size and guarded B2 patch sites.
- Five server-side fix/reference commits were verified as ancestors of published main. Pages HTTP 404 was independently rechecked. No database changes, server starts/restarts, client edits, or main promotions performed.
- The #16 report is an audit, not an AA availability policy. Release legality, ownership/refunds, a fresh backup, rollback, runtime reload and manual QA remain required for disablement.

## Publication and follow-up

The issue-review branch starts from published main and adds only the audit and documentation, in separate commits. GitHub issue comments link this report and record each closure gate. The local balance, AA ownership and PoK candidates retain their original branches and release gates. Historical docs/next-steps.md is superseded by this review where they conflict; the new next-steps document links here.

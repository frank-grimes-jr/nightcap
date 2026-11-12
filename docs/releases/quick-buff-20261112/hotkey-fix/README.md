# Quick Buff Make Hotkey follow-up

V1 owner QA: FAIL — Palwar owns rank3, but AA-window Make Hotkey is disabled. The pinned RoF2 native gate at0x6081E4 requires positive base reuse. Server-authoritative reuse remains0; only family48 wire metadata uses1, and every family48 timer packet resets `(0,current time)` so the native hotkey stays ready. Generic AA details may display nominal1second. Casting, ownership and50%maximum-mana cost remain unchanged.

**Native follow-up deployed; admissions restored. Owner visible/gameplay acceptance remains OPEN.**

PR423 merged at60d5136245e3c73a785783acfec7ed4068497065; source6c3240a2. Build reproduces current1fe268a1 full-build shipping baseline, uses its retained authoritative source including Hate223mapping and Augment icon repair, compiles AA/spells in an isolated clone with Client layout unchanged, verifies all146link inputs unchanged, and emits zone3eeb72c9adf0f7cc19baf144b1d5365d392415980eb87618774e2ae5205f4ae2. The v1 full-build requirement is retained for its original Client layout change.

Validation: native exact-client gate/receiver36checks pass after the old metadata fails; AA identity17tests pass;9restart fault tests pass on Windows and Linux. Fresh-context native and operator review found no blockers. Visible native creation, repeated activation, delivery and combined-build balance QA remain OPEN.

Deployment uses a new immutable v2 stage and one-shot operator with deployment/GM locks, zero players,125second admission drain, clean whole-game shutdown, fresh stopped full DB backup, exact normal saved-state boot and one-market-rotation checks. Client2026111201/wiki are preserved through native restart. No client payload, data/schema/rule/cache/quest change or player snapshot restore. Never replay completed terminal actions. Recover forward preserving player activity.

Wiki impact: exact613current public outputs reproduced; Combat adds corrected relog/hotkey guidance and honest nominal1second detail; Change Log records the fix; search changes.610files retained. All42authored guide/Home/Features/command/catalog and generated-page impacts reviewed; no other player-facing changes. Global source drift remains REVIEW REQUIRED. Retained artifact test_wiki had an obsolete journal-not-installed assertion; replaced only the private test with the current repository's already-correct installed-journal assertions before verification, with no public output change.

Owner QA after access reopens: relog Palwar; select Quick Buff; verify Make Hotkey enables; place it; with eligible memorized buffs and sufficient mana activate and verify instant self/group/pet delivery and one50%maximum-mana cost. Restore mana and immediately activate again, confirming no cooldown. Check unrelated AA clocks remain independent. No new client download is required for v2. Deployment and publication receipts below are separate from owner acceptance.

Independent post-release verification passes: all12zone workers run3eeb72c9, imagefaf2e410, restart count0 and native/quest/database error counts0. Signed client2026111201 is unchanged. Wiki20261112-quick-buff-v2 verifies all613HTTPS hashes/security headers and five private denials;610files retained and all five services unchanged during publication. Fresh stopped backup is retained; no player snapshot restored. Player visible hotkey/gameplay/balance acceptance remains OPEN.

# Native earned-AA bulk refund and profile-save controls

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Date: 2026-09-13. Feature branch only; no live activation or promotion.

## Result

Eleven native controls exercise 59 operations per phase. Before this increment,
seven controls fail and four pass. After it, all eleven pass. The four already
passing controls retain identical complete reports and raw report hashes.

A six-rank Natural Durability ownership costs 24 points. Starting with wallet 17,
spent 29, and expended 5, refund produces wallet 41, spent 5, and expended 5 whether
all six, only three, or zero ranks are usable. Grant-only Summon Personal Tribute
Master remains owned and in the profile. Repeated refund/reset adds no points.

An injected character-update SQL failure rolls back ownership deletion and leaves
wallet and earned ranks intact. Further save and in-place AA reload fail until a
fresh session. A separate injected committed-state disagreement leaves database
spent points at 5 and session spent points at 29; the native profile-save guard
prevents overwriting the committed counters. This is deliberate state injection,
not a network fault or full reconnect test. A valid profile save still succeeds.

The previous single-rank active/suspended reset and final-charge controls remain
unchanged. Their rollback control now requires reconnect rather than accepting an
AA-only reload, which cannot refresh character point counters.

## Evidence and provenance

Inputs, compressed native reports, build manifests, logs, exact source archives,
and the four-file server patch are retained in adjacent aa-bulk-* artifacts.
The evidence manifest records their SHA256 hashes. Both phases used the same
native diagnostic harness. The profile-save fixture explicitly sets a positive
account ID to enter the real SaveCharacterData function; it does not exercise
account authentication or the complete Client::Save caller.

A fresh build used 2,787 source files. The fourth overlay was normalized and
copied while common sources were compiling, before zone translation units.
Two subsequent small builds incorporated the in-place reload guard and immediate
failure feedback. Final source verification found no mismatches; all 87 C++ tests
pass. All 334 calculator and evidence tests also pass; their complete log is
retained as aa-bulk-python-tests.log. Final zone SHA256:
74166f07a8e7759af53f02ec9d8e75361aa89baefd95c09083b800146ea66db8.

Both clone runs removed their synthetic account, character, owned-AA, and inventory
rows and temporary failure trigger. The AA ability/rank catalog hash is unchanged.

## Remaining gates

Purchase/grant/toggle and class-release paths still require integration. Real
reconnect, uncertain COMMIT/network failures, nested transactions, and in-game QA
remain outstanding. Invalid sessions cannot save their main character row; other
earlier writes in Client::Save are not covered by this transaction. This evidence
does not establish that all AA persistence or encounter balance is complete.

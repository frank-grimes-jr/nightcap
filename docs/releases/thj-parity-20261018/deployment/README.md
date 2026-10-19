# Combined release deployment

The owner explicitly requested “Push to main and server.” PR235 promoted the
tested tree to main at `1039fdd007beb090f2830c2b546b77432c0ab0b6`.
Production is open on the verified new image. Signed game 2026101802 verifies
all 138 managed assets; wiki 20261018-thj-parity-v1 verifies all 465 public files.
Production execution and signed-client publication receipts are recorded here;
owner gameplay and balance acceptance remain separate.

The original ten-component activation uses full native world/zone/shared_memory,
the complete current signed client inventory, a fresh stopped backup and exact
whole-table content checks against a freshly rehearsed public-content clone.
Production stage: `/opt/nightcap/releases/thj-parity-20261018`.
The original `manifest.json`, component receipts and hold remain evidence.

## Reviewed startup normalization

The first boot passed native health and preserved player/custom state, then the
whole `rule_values` checksum gate held access. Exactly three new rule descriptions
were replaced by their compiled `ruletypes.h` descriptions. Values stayed true;
all other rule fields/rows and all other content tables matched. This is native
`RuleManager::UpdateInjectedRules` behavior in retained `common/rulesys.cpp`.
No production SQL repair or migration replay was necessary.

`resume_rule_notes.py prepare` authenticates exactly those three transitions on
the retained public clone, then rehearses corrected spell/heroic disable twice,
enable twice and forward again (ten checks). Generators now emit the compiled
descriptions so guarded recovery works after normal world startup. The original
and second market startup rotations are individually verified. Original player
state, cooldown receipts, owned augments and AA state are never restored.

Use **`resume_pinned.py`** as the reviewed restart entrypoint. It authenticates
and reselects the immutable new image under deployment and GM locks before
calling recovery resume. Do not invoke the lower-level resume action directly.
The recovery open action requires the matched runtime/cache/content, reviewed
hold receipts, all local hosted files and shipped-key HTTPS verification of all
138 managed client assets. Any new failure holds gateway/game again.

The preparatory `spawn2` table-name validation failure occurred before clone or
live writes; a regression covers numeric identifiers and rejects SQL injection.
The publisher and activation fault tests pass on Windows and Linux. The client
signature uses the existing local production key; it was not uploaded.

## Testing and recovery

Use [../QA.md](../QA.md) for exact item IDs, zones, spell controls, class orders,
pet lifecycle and shield tests. Reopen the normal launcher for game2026101802 /
proxy0.11.0 before testing. Classic level50 and current era/vendor gates remain.
The later level65/PoP profile is not activated. Known WPM burst and caster/pet
controller differences remain explicit balance gates in [../COMPARISON.md](../COMPARISON.md).

Use the corrected `../content/rules-disable.sql` and WPM `heroic-rule-disable.sql`
for selective formula recovery, followed by supported rule reload verification.
Numeric item recovery retains new effects and sockets. Do not revert to an
older eight-location pet binary or delete earned AA content while new state is
owned. Inspect attempted-versus-committed receipts before recovery: a failed
CREATE/CALL/DROP procedure sequence can leave a routine behind, so uncertain
components must never be blindly replayed. Preserve current player data and
prefer an authenticated forward repair.

Final operator verification: 29 tests pass on both Windows and Linux. Native
source is unchanged from the retained 47-case matrix. The final capacity check
reported 3.6 GiB free (96% used); backups and recovery images remain retained.
Check space before a future build or backup; no broad cleanup was performed.

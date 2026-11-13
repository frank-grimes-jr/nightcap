# Authorized expanded Inventory release

Owner: “Yes, implement it to match the screenshot, including the caps and combat
stats above. Use the correct server values for MIT and AVD, and publish it for
live testing.” This authorizes this scoped main promotion, paired live deployment
and client/wiki publication. It is not completed player acceptance.

Main Inventory presents HP/MP/endurance, then AC/MIT/AVD/ATK/DMG/HEAL, XP/AA XP,
seven attributes with green current, white /cap and yellow signed heroic total,
resists and weight. Preserve all equipment, bags, buttons and other tabs. Widen
the left information column and window by40px and extend its content height56px
to accommodate the four added combat rows without tiny fonts or overlaps.

AC keeps the conventional native display; no unsupported composite AC formula
is invented. MIT uses cached GetMitigationAC(), exactly as MeleeMitigation does.
AVD uses GetTotalDefense(), exactly as CheckHitChance does; -1 is shown as Auto,
not zero or a percentage. Tooltip explains opponent/situational checks. ATK is
the server conventional GetTotalATK rating, not an asserted damage-roll input.
DMG/HEAL are GetSpellDmg()/GetHealAmt() stat bonuses, not actual cast amounts.
All seven current/caps/heroics come from server getters. The displayed cap is
the actual GetMax* cap including heroic allowance, avoiding misleading subtraction
when recommended-level scaling differs from raw cap modifiers. Yellow heroics
are a component already included in the normal current/cap, not extra points to
add again. Zero displays +0; negative heroics retain their sign.

Keep NCST1 and its33fields unchanged. Capable DLLs request #nightcapui inventory;
the existing server3sec throttle returns the normal NCST1 plus a separate NCIV1
identity/sequence-protected26field Inventory snapshot. Old clients requesting
stats receive only NCST1. New client polls at most once/sec while either view is
rendered; server values expire after8sec and show -- with gray color. No player
or content/bonus calculation is changed. Preserve generic command access checks,
and make only the two internal stats subcommands bypass periodic quest/log spam.

Verify focused native collection with deliberately unequal display/raw/cached/
item/total getter values; signed sentinel, caps, protocol extremes and old/new
compatibility; hook colors/refresh/chat suppression and lifecycle; XML scope,
geometry and existing button/slot semantics. Build current retained server source
with exact predecessor reproduction; build DLL/catalog and guard exact RoF2 bytes.
Publish a higher signed counter preserving all other current client descriptors,
including Quick Buff and all prior changes. Use supported whole-runtime rollout,
admission drain, stopped backup, saved-state/market/preservation/failure-hold
guards. Preserve current wiki source/publication outside this scoped delta.

# Darthy pet summon crash â€” October 11, 2026

## Status and scope

Client proxy fix prepared on `feature/pet-summon-crash`; not installed or
published. Production and the installed `E:\Nightcap` client remain unchanged.
Owner approved main promotion and server publication on October 11, 2026.
In-game acceptance remains pending; publication evidence will be recorded below.

## Evidence

The owner reported two freezes while summoning the highest available vendor
necromancer/enchanter pets on Darthy on live Nightcap. Read-only production
inspection found character 24, level 50, NEC/MAG/ENC, in East Commonlands.
Saved spell gems were Greater Conjuration: Air (635), Kintaz's Animation (690),
and Cackling Bones (495). Saved pet records contained all three spell IDs.

The latest client log identifies Darthy in East Commonlands and records the
first access violation at client-local `16:42:00`, address `0x00AFF413`.
ECX was `0xC57B225E`, while EBX retained the pet-window pointer `0x341A6618`.
The raw stack starts with return address `0x00AFF754` and argument `4`.
With the executable loaded at `0x007F0000`, these map to preferred addresses
`0x0070F413` and `0x0070F754` in the exact pinned RoF2 executable.

At `0x70F413`, the native preference getter reads `[ECX+0x916]`. Its caller
invokes the availability predicate at `0x70F745`, then the preference getter
at `0x70F74F` without reloading ECX. The original availability predicate is a
leaf that preserves ECX/EDX. Our ordinary C++ hook calls other functions and
may overwrite those caller-volatile registers. The original regression only
checked normal calling-convention results; it missed this stronger native
contract.

After that first fault, the crash reporter faults 1,116 more times at
`0x009EAEC3`, ending at `16:48:45`. The initial failure and repeated crash
reporting explain the reported freeze/delayed error. Earlier rendering warnings
are retained in evidence but are not the fault identified by this stack.
Production logged a later link-dead client; no server restart was performed.

Local evidence is preserved under
`E:\EQ_Local_Dev\artifacts\darthy-pet-crash-20261011\`:
`dbg-before.txt`, `first-crash.txt`, `native-disassembly.txt`,
`production-inspection.json`, `installed-hashes.json`, and client configuration
and proxy log snapshots. Raw crash data stays outside Git.

## Change and verification

`PetAvailableHook` now saves ECX/EDX, passes the original self/command to the
unchanged policy, restores the registers, and removes the original four-byte
stack argument. AL retains the policy result. The server remains authoritative
for command permission and selected pets.

The x86 `/O2 /W4 /WX` regression fails on the old hook with register/stack
corruption and passes with the fix. It checks repeated fresh-roster calls,
excluded commands, native true/false results and forwarded arguments, stale
identity, mismatched identity, and empty roster fallback. The runtime suite
and exact installed-client signature verification passed. Independent review
found no implementation defect; its fallback coverage suggestion was added.

This proves the register-preservation fix in the compiled fixture. It does not
claim an observed successful pet summon in the live game.

## Release and exact owner QA

Publish only the rebuilt proxy through a new signed launcher generation, keeping
the existing catalog, configuration, UI, models, spells and server untouched.
Do not replace the installed DLL manually: the signed manifest must match it.
Capture the current hosted channel immediately before staging, retain its
assets, and compare the new inventory so only `dinput8.dll` changes. A client
that consumed a new generation needs a higher-numbered corrective release for
rollback; do not merely lower the channel number.

After approved publication, fully exit the game and update with the launcher:

1. Log Darthy into East Commonlands. Verify restored pets and the Pet Info window.
2. Dismiss and summon Cackling Bones (495), then Kintaz's Animation (690),
   then Greater Conjuration: Air (635). Repeat in reverse order, with and without
   existing pets. Include the first pet that opens the Pet Info window.
3. Switch individual pet selection and All Pets. Test follow, guard, back off,
   attack on a safe ordinary mob, and available toggles. Confirm orders reach
   the intended pets and server restrictions remain enforced.
4. Zone to West Freeport and back, then camp/relog. Verify ownership, restored
   roster, normal controls, and another summon without freezing.
5. Capture the new client log and proxy initialization evidence. Require no
   recurrence of the pet-arrival fault. Windowed mode is optional for easier
   recovery during testing; it is not the crash fix.

# Darthy pet summon crash â€” October 11, 2026

## Status and scope

Owner-approved [PR #166](https://github.com/frank-grimes-jr/nightcap/pull/166)
is merged into main (`ba3881766d50159966f0e0a98fda7dc0ac57b57d`). Signed
client release **2026101101** is published on OVH, replacing 2026101001.
On October 12, 2026, the owner confirmed that the reported pet-summon crash
is resolved after publication. This closes the reported crash; the confirmation
does not independently attest to every broader control/zone checklist step below.

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

The automated checks prove register preservation in the compiled fixture.
The subsequent owner confirmation above supplies acceptance for the reported crash.

## Publication evidence

Publication completed October 11, 2026 (America/New_York). The production
signature and all 104 hosted files (211,913,439 bytes) passed independent
verification through public HTTPS. The managed path inventory is unchanged;
only `dinput8.dll` differs from the previous release's payloads.

- DLL SHA-256: `3d5d8e5fef6a0fb96b6d2f57f8c2520a32e491544db4a9719588bfa59d54e57d`.
- Channel SHA-256: `66491d1337f3a46f40f5ea09cdb786ca5083d5c1d81f54cfbf821784e35082ea`.
- Channel expires November 11, 2026 at 00:04:10 UTC.
- Five runtime integration checks, the compiled ABI regression, and the exact
  installed RoF2 signature checks passed. All 13 publisher recovery tests passed.
  Publisher tests stub Linux directory fsync and Docker on Windows; production
  publication executes actual Linux fsync under the deployment lock.
- Reviewer feedback added bottom-up fsync for intermediate asset directories
  before the immutable release rename; its regression checks ordering.
- Service identities, image IDs, start times, restart counts and health match
  the prepublication baseline. Game/database remain healthy; no restart occurred.
- Desktop launcher channel, starter archive and guide hashes remain unchanged.

The production staging directory is
`/opt/nightcap/releases/pet-summon-crash-2026101101`. It retains the previous
channel, inventory, release audit, baseline and publication result. Local
`hosted-verification.json`, `production-after.json` and
`publisher-test-results.txt` retain verification evidence. The signed archive
SHA-256 is `ded36dcca8108590857c89fd965a60947f68a44576700688f5c5fb96c039c474`.

## Release and exact owner QA

The signed launcher generation changes only the rebuilt proxy, preserving
the existing catalog, configuration, UI, models, spells and game server.
Do not replace the installed DLL manually: the signed manifest must match it.
The predecessor channel and its assets are retained; inventory comparison
confirmed that only `dinput8.dll` changed. A client
that consumed a new generation needs a higher-numbered corrective release for
rollback; do not merely lower the channel number.

Fully exit the game and update with the launcher before this acceptance check:

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

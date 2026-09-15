# ADR 0032 - Share the client patch catalog and verify it before installation

Date: September 15, 2026. Status: accepted for the development candidate.

## Problem

The proxy and launcher must agree on the exact client and original patch bytes.
A correct download hash alone does not prove that required feature configuration
is enabled or that a catalog describes this launcher/proxy version. Previously
public installation could activate a signed generation without those checks.

## Decision

`eq-client-dll/config/patch-sites.json` is the canonical, versioned catalog for
the 22 currently recorded sites and nine existing patch groups. It contains the
exact executable identity, image base, original bytes/RVAs and known feature IDs.
`tools/generate-client-patch-catalog.py` checks it against the existing exact-client
PowerShell verifier and generates the Go embedded copy and C++ guard constants.
The verifier continues to inspect exact client bytes and source safety behavior.
Run the generator with `--check` before builds to detect drift.

Public installation requires two explicit, required entries in the already
verified signed manifest: `nightcap-patches.cfg` and `nightcap-patch-sites.json`.
Their parsed bytes must match that manifest's size/hash, and the release catalog
must be byte-identical to the compiled launcher catalog. A catalog change requires
a matching launcher/proxy build; the release minimum-launcher gate must be bumped.
Unsigned or newer metadata cannot teach an older launcher new patch sites.

Configuration is bounded UTF-8 ASCII key/value text: `schema=1`, one `0`/`1` value
per known feature, every required feature set to `1`. LF and CRLF are accepted.
Unknown/duplicate/missing keys, other values, comments, BOMs and disabled required
features fail. The optional `mq2_survey` key is explicit and defaults to `0` in the
example; this defines its upcoming runtime contract, not current DLL behavior.

Under the existing exclusive executable handle, preflight verifies regular type,
exact size/SHA256, PE32/i386 image identity and all original signatures. RVAs map
through actual PE section headers, rejecting gaps, overlapping mappings, ranges
crossing sections, zero-filled tails, overflow and truncated raw data. It never
writes the executable. The handle stays held through the transaction; existing
staged and post-replacement hash verification binds the config/catalog bytes
checked earlier to the generation marked active. Recovery remains independent
of new-release configuration so it can restore a previous generation.

## Limits and next work

`static_preflight_valid` is distinct from `ready_to_play`, which remains false.
The catalog currently describes existing hooks; it does not certify the missing
Skills/trainer/spell/AA/Bard sites or complete the production parity contract.
The proxy now consumes generated original-byte constants, but does not yet read
the configuration, emit versioned runtime health, or block startup on required
patch failure. Those behaviors and the launcher runtime handshake are still
required. Production release trust and the complete asset inventory remain
unprovisioned. No client deployment or in-game acceptance is authorized by this ADR.

## Evidence

Exact-client diagnostic and PowerShell verification pass for all 22 recorded
sites. Focused tests reject invalid configuration, altered signed preflight
assets, malformed PE headers, incorrect signatures and unsafe RVA mappings.
The x86 DLL builds and equipment-scope tests pass. Independent review found no
blocker in ordering, bounds, signed-asset binding or shared catalog generation.

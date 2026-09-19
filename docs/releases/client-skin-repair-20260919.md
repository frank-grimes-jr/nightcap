# September 19 skin-loading repair — release 2026091905

Owner QA showed the stock four-column AA window and missing AA title strings.
The running launcher was `launcher-final` release 1903, and the game reported
proxy 0.4.0 with masks 2047. More importantly, `Logs/dbg.txt` at 11:37:23 recorded
`Error loading skin "nightcap\", attempting to load default.` The owner had
selected the skin; this was an actual package defect, not just a missed command.

## Cause and repair

Python ElementTree rewrote the stock header to an `ns0:Schema` element and dropped
the otherwise unused `xmlns:dt` declaration. The exact supported client's native
parser at VA `0x8504D0` looks for literal `Schema`, then literal `xmlns` and
`xmlns:dt` attributes with values `EverQuestData` and `EverQuestDataTypes`.
Generic XML validity did not establish native compatibility.

The generator now preserves the unprefixed Schema element and both attributes,
and writes the stock ASCII XML declaration. The signed-package builder rejects
the previous representation before reading the signing key or writing a bundle.
Release 1905 retains release 1904's automatic skin selection and its 12 required
runtime features / 34 guarded patch sites. No server binary or database change
is required for this correction.

Regression evidence: the new schema test failed against the old generator, then
passed after repair. Independent disassembly and schema/reference review checked
both generated files against the exact stock UI. The real v4 asset generation is
now refused by packaging; v5 signs successfully. All four UI tests and both Go
suite configurations pass; frontend and Windows launcher builds pass. These
checks do not replace a native character login with the repaired assets.

## Delivery

The repaired build is staged at
`E:\EQ_Local_Dev\artifacts\client-repair-20260919\launcher-repair\nightcap-launcher-qa.exe`.
It contains signed release **2026091905**, expiring `2026-10-19T16:33:38Z`.
Manifest SHA256:
`293b5627c07162e2a5ff7754c79b167cf6174783541b5083f127691998ce1b3d`.

After the owner closed both applications, the existing stable launcher path
`artifacts/client-gameplay-20260919/launcher-final/nightcap-launcher-qa.exe` was
updated to 1905, with its previous executable and metadata backed up. Launcher
SHA256 is `18a21664aee4cb3c1d61cd8498325b99414b546ce5670dff761d7a8d964d0a4b`.
The separate QA client was updated with the signed installer and reached playing,
then shut down through owned cleanup. At 22:43 UTC its runtime reported proxy
0.4.1 and required/enabled/applied masks all 4095. Both installed XML files have
the repaired native header. Evidence: local `delivery-verification.json`,
`install-1905.json` and `launch-1905.jsonl` under the repair artifact directory.

Original-client installation still requires the selected authorized folder: the
repository protects `Client_RoF2_Dev` until the owner explicitly overrides that
restriction. Native character loading and gameplay acceptance remain unverified;
the new startup smoke is not a claim that those tests passed. Old offline launcher
copies embed their old packages, so Check there cannot discover a newer build.

After updating, Check must show installed release 2026091905 with every file
current. Play must report proxy 0.4.1 and required/enabled/applied masks 4095.
Login must load the Nightcap skin without a command and without a fallback line
in the new `dbg.txt` session. Check Inventory's three classes and Pet Armor tab,
then the Class column on all four AA tabs. Existing and new character profiles
must both work. The remaining [gameplay QA](client-gameplay-20260919.md) still applies.

## Separate AA string gap

The screenshot IDs 16081, 16082, 16084, 16087 and 16140 lack type-1 strings in the
client and corresponding entries in the live `db_str` table. Their `aa_ability`
names are themselves `Unknown AA ...` placeholders, sometimes class-prefixed.
This is the existing issue #16 catalog problem, not a safe source of real names.
The repair does not invent names, disable families, alter ownership or refund
points. Existing saved/system AAs remain intact; name/effect remediation needs
authoritative string data or an explicitly reviewed catalog change.

Failure evidence and the read-only catalog snapshot are preserved locally under
`artifacts/client-repair-20260919`. Earlier runtime startup success only proved
hook initialization; it did not prove that the character skin had loaded.

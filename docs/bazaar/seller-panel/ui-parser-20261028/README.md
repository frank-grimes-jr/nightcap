# Bazaar UI parser repair — 2026-10-28

## Observed defect

The owner's installed release2026102601 matched the published DLL, catalog and
Bazaar XML. UIErrors at 09:51:13 on October28 reports line1208 of
`UIFiles\nightcap\EQUI_BazaarSearchWnd.xml`: `ParseTag() Syntax Error`, followed by
`Error reading XML` and `Error loading skin: loading default skin instead`.
The label and tooltip at lines1208–1209 contained `&#8212;`. This explains missing
seller buttons and also discards unrelated Nightcap skin controls.

Original XML SHA256: `d936f54ac4d6d83d52dfe10d8502e4e26e1b552f0251e1cdbc8f47ebfa0edad4`
(35874bytes). Corrected XML SHA256:
`41fefb05f3c523ee70221329a23824834e376cf5afc2c2949deb2c33455b557e`
(35862bytes). The corrected file is exactly the original with its two `&#8212;`
references replaced by `-`. No controls or layout changed.

## Source and verification

- `tools/client_bazaar_ui.py`: ASCII heading.
- `tools/client_gameplay_assets.py::ui_xml`: explicitly encode serialized Unicode
  as ASCII, rejecting unsupported generated text instead of silently introducing
  numeric character references. Preserve lexical Schema namespace declarations.
- `tools/tests/test_client_bazaar_ui.py`: two RED then GREEN regression tests.
- Relevant suites: Bazaar5, gameplay assets6, gameplay UI5; all16 pass.
- Independent review: no blocking findings; real stock layout tested; five other
  generated UI kinds byte-identical against the previous serializer.

Standard XML validity does not establish RoF2 parser compatibility. The observed
rejection is specifically the decimal em-dash reference; ASCII-only generation
is a conservative compatibility constraint, not a claim about every entity.

## Delivery and acceptance

Source fix prepared on `fix/bazaar-ui-parser`. The weapon-conversion chat owns the
next signed client publication; it must include this XML while preserving its
new DLL and all other approved client assets. No server change or restart is
needed for this repair. Never publish an older manifest over its successor.

Local repair is pending complete EQ exit: atomic replacement was denied while
EQ held the XML open. Original installed file remains intact; backup and exact
candidate are retained privately. Do not change file permissions to bypass this.

After the coordinated client update: fully close EQ, update through the launcher,
then open `/bazaar`. Verify Search and Sell / My Listings tabs, posting quote and
confirmation, owned listing cancellation and proceeds collection. Verify a fresh
UIErrors session has no Bazaar ParseTag error or default-skin fallback. If the
saved skin remains Default, select the Nightcap skin (`/loadskin nightcap 1`).
Offline seller search/purchase and money/item correctness remain owner QA gates.
Native display acceptance and public publication are not yet established.

## Wiki impact review

This fixes delivery of already-documented controls; it changes no item, zone,
class, catalog value, command or gameplay rule. Review Features, trading guide,
troubleshooting and Recent changes against the current wiki checkout. Add a
client-update troubleshooting note and release correction with the coordinated
publication; retain live-QA labels. Coordinate with the weapon chat's wiki work.

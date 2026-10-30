# Candidate review

Reviewed against the owner's delayed cast-bar report and the current integrated
source/public spell asset. Review was performed in separate correctness,
scope/preservation and release/privacy passes by the implementing agent; it is
not an independent reviewer or owner approval.

- Root cause is supported by actual pinned native instructions, current public
  file bytes, read-only production content, and the exact native RED/GREEN run.
  The test's initial lookup ABI fixture fault was corrected before recorded runs.
- Repair changes only 638 reviewed timing fields. All other fields, line endings,
  40,105 other rows and later custom spell additions survive byte-for-byte.
  The catalog excludes intentional DoTs/Bard overrides; server/focus semantics
  and character access are unchanged. Unknown future 50-ms spells are preserved.
- Missing IDs, duplicates, malformed rows and unexpected names/times fail closed.
  Already corrected input is idempotent. CLI output cannot overwrite the input
  client tree and uses exclusive creation. No runtime/process writes occur.
- Native gauge: existing public file has 2752 failures out of 5105 assertions;
  corrected file has zero. Scope includes ordinary progress, zero base times,
  expiry, cancellation and absent player. Actual rendering/packets/focus remain QA.
- Client asset suite: 39 tests, 37 pass and two environment-dependent skips.
  An initial sandbox run failed four temporary-directory fixtures; the same suite
  passes outside that restriction. Wiki/content/refresh: 19 pass; 492 pages build.
  The refresh negative test intentionally emits `fatal: Needed a single revision`.
- Normal generation from the preserved input retains all 638 corrected times.
  Existing inability to ingest later custom spell 43220 is documented; publishing
  a whole regenerated spell file would be unsafe. Use only the one-file transform
  on authenticated current release bytes.
- Wiki review covers all 40 maintained articles and generated catalog impact.
  Three pages gain explicit Not released notes; existing text/status is preserved.
  The 500 historically drifted source paths remain REVIEW REQUIRED, with no
  blanket advance or unrelated publication claim.
- No credentials, character snapshot or raw private capture is committed. No
  protected client changes, SQL writes, runtime restart or publication occurred.

No blocking defect was found in the scoped candidate. Signed delivery and
main promotion require owner authorization; visible gameplay remains unaccepted.

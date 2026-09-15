# ADR 0027: Trusted client release metadata before activation

Date: September 15, 2026. Status: implemented initial verifier; delivery continues.
Issues: #10, #14, #15. Implements the existing approved multiclass contract.

## Decision

Build the new Go launcher core in `eq-launcher/`; adapt the Wails shell from the
expansion switcher after its sync engine is safe. Do not reuse direct-to-client
unsigned download/replacement code. Authenticate metadata before any download
entry or client path is trusted.

Schema 1 canonical bytes are the compact Go JSON encoding of the fixed Manifest
struct, in declaration order, with standard JSON escaping, RFC3339 time encoding
and no trailing newline. Sign these exact bytes with Ed25519; a detached
signature identifies a separately trusted key. Re-encoding must match exactly,
so unknown fields, duplicate keys and alternative spellings fail. This is a
schema-specific encoding, not a claim to implement RFC 8785/JCS.

The release inventory/required flags, allowed hosts, key validity and persisted
highest release/digest belong to trusted launcher state. A manifest cannot grant
itself permission to manage a path or choose its own trust key. Lower release
IDs fail; the same ID must have identical bytes, permitting repair of the same
trusted generation. A new release ID is required to change or renew metadata.

Paths use lowercase ASCII slash-separated names to eliminate Windows aliasing.
Reserve game executables, player config and updater state. Assets/tombstones must
match exact trusted ownership lists. Schema 1 does not allow signed URL queries
or custom ports. Network redirects still need independent host checks in the
future downloader; validating the initial URL does not validate a redirect.

## Threats and remaining obligations

The verifier rejects metadata tampering, unknown/expired keys, replay downgrade,
path traversal/ADS/device names, foreign files and excessive sizes. Filesystem
junctions, concurrent file replacement, staging integrity, durable anti-rollback
state, journal recovery, signed rollback, key rotation and required patch health
remain responsibilities of later slices. No installer/Play action exists yet.
The diagnostic authenticates only the supported executable and does not claim
client parity or a valid installed generation.

## Evidence

Tests exercise signature/key/time/version failures, alternate JSON encodings,
inventory completeness and required flags, Windows path aliases, file size/hash,
HTTPS destinations and tombstone ownership. The first test run failed for missing
implementation; the verifier then passed. Existing exact-client patch-site checks
also pass against the unchanged local RoF2 executable.

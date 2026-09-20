# Classic Lavastorm client prerequisite

September 20, 2026. The owner approved preparing an update for the separate QA
client only. No client files have been changed for this prerequisite.

The following inspected clients contain revamped `lavastorm.eqg` and supporting
archives, but none contains the required Classic `lavastorm.s3d`:

- `E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2` (original; leave untouched).
- `E:/EQ_Local_Dev/artifacts/client-gameplay-20260919/client` (approved QA target).
- `E:/EQ_Local/Client_RoF2/everquest_rof2` (owner-suggested read-only source).

The recursive search of `E:/EQ_Local` also found no ZIP/7z/RAR/ISO client archive;
the CABs present are DirectX redistributables, not game terrain.

The [FV Project zone repair listing](https://fvproject.com/index.php/Zone_Files)
describes a Classic Lavastorm package, but direct HTTPS retrieval failed with an
expired certificate and HTTP returned 500. Certificate checks were not disabled.
Do not substitute unverified geometry or rename away the current terrain before
the complete Classic replacement is available.

Next steps once the owner supplies a working Classic client/archive:

1. Read the source without modifying it; stage the Lavastorm assets separately
   and record their hashes and provenance. Inspect archive contents and compare
   the actual ring geometry with the configured server map.
2. Add the reviewed assets and pinned retirement of revamped `lavastorm.eqg` to
   the existing signed QA client release mechanism. Retain a rollback copy and
   refuse changed preimages. Leave the original client untouched.
3. Verify the separate QA client loads Classic Lavastorm and renders the ring at
   world X=1389,Y=1014,Z=131 with safe footing. Server collision geometry alone
   is insufficient evidence.
4. Keep `nightcap:classic_lavastorm_client_ready` absent until readiness applies
   to every client allowed to use the port. It is a global gate, not per-client
   capability detection. Then recheck menu and stale-link behavior.

Until then Khalure offers the other eight Classic rings. The map alias repair
does not remove this client prerequisite or constitute manual gameplay acceptance.

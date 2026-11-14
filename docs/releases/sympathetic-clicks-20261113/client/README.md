# Classic sympathetic click client release

Game release 2026111301 uses signed parent 2026111202. The spell and string files append identities 44379 and 44380. The other 146 file descriptors retain their original URLs, hashes and sizes. Fully exit EverQuest and use launcher Play.

## Prepare

Build the two Go sources separately from temporary command directories inside the eq-launcher module so they import the shipped manifest and preflight packages. Download the canonical parent channel. Run prepare_client with the parent envelope, verified parent config/catalog/proxy, the exact RoF2 executable directory, the tested client-v3 assets, the local production signing seed, and an exclusive output path. The tool checks the parent envelope pin, shipped signing key, full inventory, proxy/config/catalog pairing and the two tested asset pins. The release expiry is fixed for reproducibility. The signing seed stays on the signing host.

Run verify_client with the previous and expected envelopes. Run test_publish.py in a POSIX environment for permission, fsync, interrupted-write and drift cases. Stage the two signed assets, envelopes, verification receipt and pinned publish.py under the private release stage's client directory. This step leaves the public channel at its parent.

## Coordinated activation and recovery

The paired operator holds both deployment locks. It first verifies the running native candidate, database afterimages, cache and closed admissions. It calls publish(stage_client, public_root, snapshot) with an enforced closed-admissions snapshot. The publisher rehashes the 146 inherited assets and both replacements and switches the channel with an atomic rename. The operator keeps admissions closed through independent canonical HTTPS verification. Run verify_client with -hosted to verify the public envelope, all 148 canonical downloads, size, SHA-256, history, retained policy and the proxy/catalog pair. On interruption, inspect the actual public channel and immutable release bytes before choosing a recovery step.

Prior to a channel switch, a failed preflight or interrupted asset write leaves the previous channel usable. After any public exposure, preserve downloaded files and signed history. A client correction needs a higher signed counter over the visible release and must remain paired with the native/content recovery. Never restore the old pointer over clients that may have observed the higher release. A deployed client check does not establish player encounter or UI acceptance.

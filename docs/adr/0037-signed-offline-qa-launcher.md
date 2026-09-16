# 0037: Embed a signed offline QA release

Date: 2026-09-15. Status: accepted for local QA.

## Context

The desktop preview recognized RoF2 but had no configured release source, keys,
or Play authorization. The owner requested a usable patching and launch package.
A hosted production channel and full client gameplay acceptance remain separate.

## Decision

Generate a `qacandidate` policy and embed a canonical Ed25519-signed four-file
release. Normal builds use mutually exclusive `!qacandidate` policy with no
release authority. QA uses the same manifest verifier, complete-generation
staging, journaled installer, launch lease, bootstrap and process-bound health.
Embedded manifests use `qa.nightcap.invalid` as a reserved namespace; neither
metadata nor asset retrieval falls back to HTTP.

Keep QA settings/staging beside the executable and use a full independent copy
of the existing RoF2 client. Distinguish the window, UI, file metadata and singleton
identity from the development preview. Generated bundle/policy are ignored;
retain the private signing seed in a restricted directory outside source/package.

## Consequences

The QA executable installs/repairs its embedded release offline. A newer patch
requires a newly assembled QA executable with a higher release number; this does
not establish a hosted updater. Manifest expiry and all signature/runtime checks
remain enforced. The local package is signed at the manifest level, not Windows
Authenticode-signed. Gameplay QA and production distribution remain open.

Windows job accounting can reach zero before the image mapping disappears.
Session completion probes writable-open without writing bytes, waits at most five
seconds for transient teardown, and reports a persistent external lock as cleanup
failure. Actual process termination remains mandatory before lease release.

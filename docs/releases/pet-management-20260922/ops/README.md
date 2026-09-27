# Pet release operations

These are the exact reviewed rollout/publication helpers for the September 22
paired release. They are pinned to its private OVH staging paths and manifests;
they are not general deployment commands. Private SQL backups and credentials
are excluded from the repository. See the adjacent release record for activation
evidence and paired recovery instructions.

Run the 47 isolated failure/replay tests from this directory:

```powershell
python -m unittest test_rollout.py test_publish.py test_desktop.py
```

Tests replace Docker, database and publication boundaries with disposable state.
They must never access the live host. `fetch-evidence.py` exports only hashes,
counts and health information from a completed host rollout.

---
name: release-switcher
description: Build and release the eq-expansion-switcher Wails Windows desktop app. Use when the user wants to build locally or publish a new release.
disable-model-invocation: true
---

Build or release eq-expansion-switcher from the `eq-expansion-switcher/` directory.

Ask the user which type of build they want if not specified in $ARGUMENTS:

**Local dev build** (test before releasing):
```powershell
cd eq-expansion-switcher
wails build -platform=windows/amd64
```
Output goes to `build/bin/`. Test the binary before releasing.

**Full release** (Drone CI + GitHub release):
```powershell
cd eq-expansion-switcher
make ci-build
```
Requires `GH_RELEASE_GITHUB_API_TOKEN` set in `eq-expansion-switcher/.env`.
This builds, tags, and publishes a GitHub release via Drone.io.

**Docker image** (if updating the build image):
```powershell
cd eq-expansion-switcher
make image-build
# then: make image-publish
```

Before a full release, confirm the version has been bumped in the appropriate config file and the local build works cleanly.

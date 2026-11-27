# November 27 Classic QA release operations

The LocalDev and OVH preflight found twelve zone workers running the same zone executable on each server. Both environments had zero connected players when sampled. The zone SHA-256 begins `34de795f`. Both scoped quest files and the spell caches match. Each server keeps its own item cache. The November 25 sympathetic item changes account for the newer OVH release. See [captured hashes and process counts](baseline.json).

The server package includes the Cazic and Recall quest changes, the rebuilt zone, Cazic's NPC row 72003 and the class mask for AA family 2220. The image derives from the running game's own immutable parent. The quest packager applies each committed hunk once to the captured active script, so line endings and surrounding deployed edits survive. The LocalDev and OVH `classes` columns are both `int(10)`. The standalone Recall rehearsal on both servers changed one temporary row, a repeat changed zero, and the inverse restored the original mask. The full operator applies the NPC stats and Recall mask together in one transaction.

## Running a release

1. Use `capture.py TARGET STAGE` from this checkout to capture each environment into a separate private directory. The target is `local` or `production`. The capture script uses the runtime world interface for occupancy.
2. Use `package.py STAGE ZONE_FILE ZONE_SHA BASE_COMMIT SOURCE_COMMIT` with the tested executable and committed source. The release manifest fingerprints scripts, the prior and proposed quest files, caches, image and binaries.
3. For LocalDev, run the packaged `release.py prepare`. For OVH, run `upload.py STAGE upload`, then `upload.py STAGE prepare` here. Preparation builds the zone-only image, validates the Lua syntax and rehearses the forward and inverse SQL against session-local copies of both tables.
4. Once the package has passed verification and has release authorization, run the packaged LocalDev `release.py activate` or `upload.py STAGE activate` for OVH. Activation checks zero players, closes admissions, stops the full game cleanly and creates a verified PEQ dump. It switches the scoped rows and files, starts the game and verifies five native hashes, mapped workers, both caches, quest contents, the Recall mask and occupancy. OVH reopens the gateway after verification. Inspect the terminal receipt before considering a retry.
5. The `verify` action repeats runtime checks. The `rollback` action checks the candidate state and zero occupancy, obtains a new backup, and restores the previous image, two prior quests and both prior content rows. Player state stays current. A failed operation with a started receipt must be reconciled against the current running state before another attempt.

## Optional Hailstone preview

`build_preview.py` checks the retained executable's code section against a fresh baseline link, applies the class-17 AA mask patch and tests the resulting predicates and AA timer behavior. It emits the updated GUI, its corresponding source archive and a private read-only LocalDev probe. `build_desktop.py` retains the deployed frontend assets, builds the production launcher with the new preview and verifies its signed envelope. `publish_preview.py` stages and verifies the immutable files before advancing the independent desktop channel.

After activating LocalDev, `verify_recall.ps1 candidate` uses the existing disposable level-one Dwarf Cairnwright, the loopback login server and the new diagnostic client. It checks the General tab's exact filtered list and the client's earned rank twice across fresh login and camp. The test reads the two label sources and compares the character's saved rank and AA points.

The operator checks deployed state. Visible hotbar behavior, live item display and encounter tuning still require the player checks in the release report.


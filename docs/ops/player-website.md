# Player website and GitHub Pages

The owner explicitly authorized updating the HTML/documentation and public
GitHub Pages publication on September 15, 2026. The earlier automatic-review
block is superseded by that specific approval.

## Content contract

`index.html` is a self-contained player guide: Home, Features, Major Changes and
FAQ tabs. No framework build, external fonts, tracking scripts, account form or
client download is required. Copy follows deployed behavior and clearly labels
live testing and unfinished features. Current internal status belongs in
[status.md](../status.md); technical deployment details stay off the player page.

## Publication

Public destination: https://frank-grimes-jr.github.io/nightcap/.
Publish only reviewed `index.html` and `.nojekyll` on the dedicated `gh-pages`
branch. Configure Pages to that branch, root directory. This payload excludes
server sources, database backups and local artifacts and does not promote gameplay
to main. Keep the canonical HTML in the normal feature/dev/test history.

For an update: review actual gameplay statements, run browser checks, copy the
exact HTML bytes to the Pages branch, commit/push, wait for a successful build,
then fetch the public URL and compare its SHA256 to the source. Verify all four
tabs, keyboard navigation, FAQ disclosure and small-screen layout publicly.
A pushed branch alone is not proof of a successful deployment.

## Verification and rollback

Browser checks cover tab selection, arrow/Home/End keys, direct fragment links,
browser history, FAQ disclosure, no-JavaScript readability and narrow viewports.
Publication evidence will be recorded below after the build succeeds.
Rollback by restoring the last verified static commit on `gh-pages` with a new
commit, then repeat the public hash/browser checks. Gameplay deployment and QA
remain independent of this site.

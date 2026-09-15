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
Publication evidence is recorded below; GitHub rejected site activation.
Rollback by restoring the last verified static commit on `gh-pages` with a new
commit, then repeat the public hash/browser checks. Gameplay deployment and QA
remain independent of this site.

## September 15 publication result

- Source implementation: `9f6f48b`; reviewed PR #50 merged to dev and test at
  `2d95329`. Main gameplay was not promoted.
- Static branch: `gh-pages`, commit `e6efdf1`; exactly `index.html` and `.nojekyll`.
- Local browser suite and desktop/mobile visual inspection passed.
- POST `/repos/frank-grimes-jr/nightcap/pages` returned HTTP 422:
  `Your current plan does not support GitHub Pages for this repository.`
- The repository is private. Follow-up Pages GET still returns 404. The proposed
  public URL is **not live**; no public hash/browser verification is claimed.
- Issue #23 remains open. Hosting requires a supported GitHub plan or an
  owner-selected alternate destination, such as a public website-only repository.
  Publication authorization is present; the remaining blocker is GitHub plan support.

Run the browser suite from the repository root with Node:

```powershell
node tools/tests/test_player_site.cjs
```

Install/provide Playwright through `PLAYWRIGHT_MODULE` if it is outside normal
Node resolution; `BROWSER_EXECUTABLE` selects an installed Chromium browser.
`SCREENSHOT_DIR` saves visual evidence. Set `SITE_URL` to test the deployed URL
once hosting succeeds. No server restart is needed for website updates.

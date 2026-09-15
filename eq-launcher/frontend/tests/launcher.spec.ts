import { test, expect, type Page } from "@playwright/test";
import type { Status } from "../src/bridge";

async function desktop(
  page: Page,
  mode: "normal" | "cancel" | "recovery" | "error" | "play" = "normal",
) {
  await page.addInitScript((mode) => {
    const state = {
      client_dir: "",
      phase: "choose",
      message: "Choose your EverQuest folder to begin.",
      supported: false,
      configured: true,
      busy: false,
      release: 0,
      installed_release: 0,
      recovery_required: false,
      files: [],
      remove: [],
      events: [],
      can_check: false,
      can_update: false,
      can_recover: false,
      can_play: false,
    } as Status;
    let finishUpdate: undefined | (() => void);
    let finishPlay: undefined | (() => void);
    const event = (message: string) =>
      state.events.push({ time: "12:34:56", message });
    window.go = {
      main: {
        App: {
          async GetStatus() {
            return structuredClone(state);
          },
          async ChooseClient() {
            Object.assign(state, {
              client_dir: "E:/Games/EverQuest",
              supported: true,
              phase: "selected",
              message: "Client recognized. Check for a verified release.",
              can_check: true,
            });
            event("Selected client folder.");
          },
          async CheckForUpdates() {
            if (mode === "error")
              throw new Error('<img src=x onerror="window.injected=true">');
            if (mode === "recovery") {
              Object.assign(state, {
                phase: "recovery",
                message:
                  "An interrupted update needs recovery before continuing.",
                recovery_required: true,
                can_recover: true,
                can_update: false,
              });
              return;
            }
            Object.assign(state, {
              phase: "update",
              message: "Release 2 is ready. 2 file changes to apply.",
              release: 2,
              files: [
                { path: "dinput8.dll", state: "missing" },
                { path: "uifiles/nightcap/window.xml", state: "current" },
              ],
              remove: ["old.dll"],
              can_update: true,
            });
            event("Verified signed release 2.");
            if (mode === "play") Object.assign(state, {can_play: true, installed_release: 2, phase: "health_pending", files: state.files.map((f) => ({...f, state: "current"})), remove: []});
          },
          async Update() {
            Object.assign(state, {
              phase: "staging",
              message: "Preparing and verifying all release files…",
              busy: true,
              can_check: false,
              can_update: false,
            });
            if (mode === "cancel") {
              await new Promise<void>((resolve) => {
                finishUpdate = resolve;
              });
              return;
            }
            Object.assign(state, {
              phase: "health_pending",
              message:
                "Files installed. Client compatibility checks are still required before Play.",
              busy: false,
              installed_release: 2,
              can_check: true,
              can_update: true,
              files: state.files.map((f) => ({ ...f, state: "current" })),
              remove: [],
            });
            event("Files installed.");
          },
          async Play() {
            Object.assign(state, {phase:"playing",message:"Nightcap is running. Keep this launcher open while playing.",busy:true,can_play:false,can_check:false,can_update:false});
            await new Promise<void>((resolve) => {finishPlay=resolve;});
          },
          async Cancel() {
            if (finishPlay) {
              Object.assign(state, {phase:"stopping",message:"Stopping Nightcap. Keep the launcher open until cleanup finishes."});
              await new Promise((resolve) => setTimeout(resolve, 100));
              Object.assign(state, {phase:"stopped",message:"Nightcap closed. You can launch again or close the launcher.",busy:false,can_check:true,can_play:true});
              finishPlay();
              return;
            }
            Object.assign(state, {
              phase: "error",
              message: "Operation cancelled.",
              busy: false,
              can_check: true,
            });
            finishUpdate?.();
          },
          async Recover() {
            Object.assign(state, {
              phase: "selected",
              message: "Recovery completed. Check for updates to continue.",
              recovery_required: false,
              can_recover: false,
            });
            event("Recovery completed.");
          },
          async OpenGuide() {},
        },
      },
    };
  }, mode);
  await page.goto("/");
  await page
    .getByRole("button", { name: "Choose client folder", exact: true })
    .click();
  await expect(page.getByText("Supported RoF2", { exact: true })).toBeVisible();
}

test("browser preview has no native actions or launch authority", async ({
  page,
}) => {
  const failures: string[] = [];
  page.on("pageerror", (e) => failures.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Launcher preview", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Choose client folder", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Play Nightcap" }),
  ).toBeDisabled();
  await page.screenshot({
    path: "test-results/launcher-preview.png",
    fullPage: true,
  });
  expect(failures).toEqual([]);
});

test("selected client, verified inventory, update, activity and Play gate", async ({
  page,
}) => {
  await desktop(page);
  await page
    .getByRole("button", { name: "Check for updates", exact: true })
    .click();
  await expect(page.getByText("dinput8.dll", { exact: true })).toBeVisible();
  await expect(page.getByText("Remove", { exact: true })).toBeVisible();
  await page.screenshot({
    path: "test-results/launcher-update.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Install update", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Files verified", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Play Nightcap" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: /Activity/ }).click();
  await expect(
    page.getByText("Files installed.", { exact: true }),
  ).toBeVisible();
});

test("cancel remains clickable while native Update promise is pending", async ({
  page,
}) => {
  await desktop(page, "cancel");
  await page
    .getByRole("button", { name: "Check for updates", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Install update", exact: true })
    .click();
  await expect(page.getByRole("progressbar")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Change folder", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(page.getByRole("status")).toHaveText("Operation cancelled.");
  await expect(page.getByRole("progressbar")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Check for updates", exact: true }),
  ).toBeEnabled();
});

test("pending recovery blocks update and restores check action", async ({
  page,
}) => {
  await desktop(page, "recovery");
  await page
    .getByRole("button", { name: "Check for updates", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Install update", exact: true }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Recover previous files", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Recovery completed.");
  await expect(
    page.getByRole("button", { name: "Play Nightcap" }),
  ).toBeDisabled();
});

test("native errors are escaped and keyboard navigation remains available", async ({
  page,
}) => {
  await desktop(page, "error");
  await page
    .getByRole("button", { name: "Check for updates", exact: true })
    .click();
  await expect(page.getByRole("alert")).toHaveText(
    '<img src=x onerror="window.injected=true">',
  );
  await expect(page.locator("img")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Change folder", exact: true })
    .focus();
  await expect(
    page.getByRole("button", { name: "Change folder", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("narrow layout has no horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 640, height: 900 });
  await desktop(page);
  await page
    .getByRole("button", { name: "Check for updates", exact: true })
    .click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/launcher-narrow.png",
    fullPage: true,
  });
});


test("Play remains pending while Stop game stays available and edits are locked", async ({page}) => {
  const failures: string[] = [];
  page.on("pageerror", (e) => failures.push(e.message));
  await desktop(page, "play");
  await page.getByRole("button", {name:"Check for updates",exact:true}).click();
  await expect(page.getByRole("button", {name:"Play Nightcap"})).toBeEnabled();
  await page.getByRole("button", {name:"Play Nightcap"}).click();
  await expect(page.getByRole("heading", {name:"Nightcap is running",exact:true})).toBeVisible();
  await expect(page.getByRole("button", {name:"Change folder",exact:true})).toBeDisabled();
  await expect(page.getByRole("button", {name:"Check for updates",exact:true})).toBeDisabled();
  await expect(page.getByRole("button", {name:"Play Nightcap"})).toBeDisabled();
  await expect(page.getByRole("progressbar")).toHaveCount(0);
  await page.screenshot({path:"test-results/launcher-playing.png",fullPage:true});
  await page.getByRole("button", {name:"Stop game",exact:true}).click();
  await expect(page.getByRole("heading", {name:"Nightcap closed",exact:true})).toBeVisible();
  await expect(page.getByRole("button", {name:"Play Nightcap"})).toBeEnabled();
  expect(failures).toEqual([]);
});

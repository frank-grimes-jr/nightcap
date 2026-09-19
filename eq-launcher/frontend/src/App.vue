<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { initial, invoke, native, snapshot, type NativeAPI } from "./bridge";
const state = ref({ ...initial });
const pending = ref(false);
const cancelling = ref(false);
const error = ref("");
const tab = ref<"client" | "activity">("client");
let timer: ReturnType<typeof setInterval> | undefined;
let reading = false;
const busy = computed(() => pending.value || state.value.busy);
const titles: Record<string, string> = {
  choose: "Choose your client",
  selected: "Check your client",
  checking: "Checking your release",
  update: "An update is ready",
  staging: "Preparing your update",
  installing: "Installing your update",
  recovering: "Restoring your client",
  recovery: "Recovery needed",
  health_pending: "Files verified",
  launching: "Starting Nightcap",
  playing: "Nightcap is running",
  stopping: "Stopping Nightcap",
  stopped: "Nightcap closed",
  preview: "Client recognized",
  browser_preview: "Launcher preview",
  error: "Action needed",
};
const title = computed(() => titles[state.value.phase] ?? "Client status");
const rows = computed(() => [
  ...state.value.files.map((f) => ({
    path: f.path,
    action: { current: "Verified", changed: "Replace", missing: "Download" }[
      f.state
    ],
  })),
  ...state.value.remove.map((path) => ({ path, action: "Remove" })),
]);
const changeCount = computed(
  () =>
    state.value.files.filter((f) => f.state !== "current").length +
    state.value.remove.length,
);
async function refresh() {
  if (reading) return;
  reading = true;
  try {
    state.value = await snapshot();
  } catch (e) {
    error.value = String(e);
  } finally {
    reading = false;
  }
}
async function run(action: Exclude<keyof NativeAPI, "GetStatus" | "Cancel">) {
  if (busy.value) return;
  pending.value = true;
  error.value = "";
  try {
    await invoke(action);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    pending.value = false;
    await refresh();
  }
}
async function cancel() {
  if (cancelling.value) return;
  cancelling.value = true;
  try {
    await invoke("Cancel");
  } catch (e) {
    error.value = String(e);
  } finally {
    cancelling.value = false;
    await refresh();
  }
}
onMounted(async () => {
  await refresh();
  timer = setInterval(refresh, 400);
});
onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <svg viewBox="0 0 40 40" aria-hidden="true">
          <path
            d="M30 29A16 16 0 0 1 13 5 16 16 0 1 0 30 29Z"
            fill="currentColor"
          />
          <circle cx="29" cy="10" r="2" fill="currentColor" />
        </svg>
        <div>NIGHTCAP<span>EVERQUEST</span></div>
      </div>
      <nav aria-label="Launcher sections">
        <button
          :class="{ selected: tab === 'client' }"
          @click="tab = 'client'"
          :aria-current="tab === 'client' ? 'page' : undefined"
        >
          <span aria-hidden="true">◈</span> Client</button
        ><button
          :class="{ selected: tab === 'activity' }"
          @click="tab = 'activity'"
          :aria-current="tab === 'activity' ? 'page' : undefined"
        >
          <span aria-hidden="true">≡</span> Activity
          <small v-if="state.events.length">{{ state.events.length }}</small>
        </button>
      </nav>
      <div class="sidebar-bottom">
        <p>Solo-preferred.<br />Adventure earned.</p>
        <button
          class="guide"
          @click="run('OpenGuide')"
          :disabled="!native() || busy"
        >
          Player guide <span aria-hidden="true">↗</span></button
        ><span class="build">Launcher 0.1.0 · {{ state.channel }}</span>
      </div>
    </aside>
    <main>
      <header class="page-heading">
        <div>
          <p class="eyebrow">WELCOME TO NIGHTCAP</p>
          <h1>{{ tab === "client" ? "Your client" : "Recent activity" }}</h1>
        </div>
        <span class="preview-badge">{{ state.channel || "Development preview" }}</span>
      </header>
      <template v-if="tab === 'client'">
        <section
          class="status-panel"
          :class="{
            attention: state.phase === 'error' || state.recovery_required,
          }"
          aria-labelledby="status-title"
        >
          <div class="status-heading">
            <span
              class="status-symbol"
              :class="{ working: state.busy }"
              aria-hidden="true"
              >{{
                state.busy ? "◌" : state.recovery_required ? "!" : "◈"
              }}</span
            >
            <div>
              <p class="eyebrow">CLIENT STATUS</p>
              <h2 id="status-title">{{ title }}</h2>
            </div>
          </div>
          <p class="status-message" role="status" aria-live="polite">
            {{ state.message }}
          </p>
          <p v-if="state.can_play" class="status-message">
            In game, run <code>/loadskin nightcap 1</code> once per character to show
            the three classes, AA class column, and Pet Armor tab.
          </p>
          <p v-if="error" class="error-message" role="alert">{{ error }}</p>
          <div
            class="progress"
            v-if="state.busy && state.phase !== 'playing'"
            role="progressbar"
            aria-label="Client operation in progress"
          >
            <span></span>
          </div>
          <div class="actions">
            <button
              class="primary"
              v-if="!state.client_dir"
              @click="run('ChooseClient')"
              :disabled="!native() || busy"
            >
              Choose client folder</button
            ><button
              class="primary"
              v-else-if="state.recovery_required"
              @click="run('Recover')"
              :disabled="!state.can_recover || busy"
            >
              Recover previous files</button
            ><button
              class="primary"
              v-else-if="state.can_update"
              @click="run('Update')"
              :disabled="busy"
            >
              {{ changeCount ? "Install update" : "Repair files" }}</button
            ><button
              class="primary"
              v-else
              @click="run('CheckForUpdates')"
              :disabled="!state.can_check || busy"
            >
              Check for updates</button
            ><button
              class="secondary"
              v-if="state.can_update"
              @click="run('CheckForUpdates')"
              :disabled="busy"
            >
              Check again</button
            ><button
              class="secondary"
              v-if="state.busy && state.phase !== 'recovering'"
              @click="cancel"
              :disabled="cancelling || state.phase === 'stopping'"
            >
              {{ state.phase === "playing" ? "Stop game" : state.phase === "stopping" ? "Stopping…" : "Cancel" }}
            </button>
          </div>
        </section>
        <section class="details" aria-labelledby="folder-title">
          <div class="section-heading">
            <h2 id="folder-title">EverQuest folder</h2>
            <button
              class="text-button"
              @click="run('ChooseClient')"
              :disabled="!native() || busy"
            >
              {{ state.client_dir ? "Change folder" : "Browse…" }}
            </button>
          </div>
          <div class="folder-path">
            <span aria-hidden="true">▱</span
            ><code>{{ state.client_dir || "No client folder selected" }}</code>
          </div>
          <dl class="facts">
            <div>
              <dt>Client</dt>
              <dd>
                {{
                  state.supported
                    ? "Supported RoF2"
                    : state.client_dir
                      ? "Not verified"
                      : "Not selected"
                }}
              </dd>
            </div>
            <div>
              <dt>Installed release</dt>
              <dd>{{ state.installed_release || "Not installed" }}</dd>
            </div>
            <div>
              <dt>Available release</dt>
              <dd>{{ state.release || "Not checked" }}</dd>
            </div>
          </dl>
        </section>
        <section class="details inventory" aria-labelledby="files-title">
          <div class="section-heading">
            <h2 id="files-title">Release files</h2>
            <span class="muted">{{
              rows.length ? `${rows.length} files` : "No release selected"
            }}</span>
          </div>
          <div class="empty" v-if="!rows.length">
            <span aria-hidden="true">◇</span>
            <div>
              <p>Your files will appear here</p>
              <small
                >Choose your client, then check for an available release.</small
              >
            </div>
          </div>
          <div class="file-scroll" v-else>
            <table>
              <thead>
                <tr>
                  <th scope="col">File</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="file in rows" :key="file.path">
                  <td>
                    <code>{{ file.path }}</code>
                  </td>
                  <td>
                    <span
                      class="file-action"
                      :class="{ verified: file.action === 'Verified' }"
                      >{{ file.action }}</span
                    >
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
      <section class="details activity" v-else aria-labelledby="activity-title">
        <div class="section-heading">
          <h2 id="activity-title">This session</h2>
          <span class="muted">Latest {{ state.events.length }} events</span>
        </div>
        <p class="empty" v-if="!state.events.length">
          Client checks and update results will appear here.
        </p>
        <ol v-else>
          <li v-for="(event, i) in state.events" :key="i">
            <time>{{ event.time }}</time>
            <p>{{ event.message }}</p>
          </li>
        </ol>
      </section>
      <footer class="play-bar">
        <div>
          <strong>{{ state.phase === "playing" ? "Your session is running" : state.phase === "stopping" ? "Finishing your session" : state.can_play ? "Launch your installed release" : "Play is not available yet" }}</strong>
          <p>{{ state.phase === "playing" || state.phase === "stopping" ? "Keep the launcher open until your game session ends." : state.can_play ? "Your files and client compatibility will be verified before launch." : "Client compatibility and release checks must pass first." }}</p>
        </div>
        <button class="play-button" @click="run('Play')" :disabled="!native() || !state.can_play || busy" aria-describedby="play-reason">
          Play Nightcap <span aria-hidden="true">→</span></button
        ><span id="play-reason" class="sr-only"
          >{{ state.can_play ? "Launch with fresh release and client checks." : "Game launch is unavailable while checks or another operation are pending." }}</span
        >
      </footer>
    </main>
  </div>
</template>

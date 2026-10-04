<script setup>
import { onMounted, ref, watch } from "vue";
import { api } from "./api.js";
import NpcWorkspace from "./components/NpcWorkspace.vue";
import RecordEditor from "./components/RecordEditor.vue";
import ChangeReview from "./components/ChangeReview.vue";
import HistoryView from "./components/HistoryView.vue";

const meta = ref(null),
  target = ref(""),
  page = ref("browse"),
  draft = ref(null),
  drafts = ref([]),
  editor = ref(null);
const error = ref(""),
  notice = ref(""),
  connected = ref(false),
  connecting = ref(false),
  refreshKey = ref(0),
  saving = ref(false);
let connectionSequence = 0;
async function run(work) {
  error.value = "";
  try {
    return await work();
  } catch (e) {
    error.value = e.message;
  }
}
async function refreshDrafts() {
  drafts.value = await api("/drafts");
}
async function connect() {
  const sequence = ++connectionSequence;
  connected.value = false;
  if (!target.value) return;
  connecting.value = true;
  error.value = "";
  try {
    await api(`/targets/${target.value}/status`);
    if (sequence === connectionSequence) connected.value = true;
  } catch (e) {
    if (sequence === connectionSequence) error.value = e.message;
  } finally {
    if (sequence === connectionSequence) connecting.value = false;
  }
}
async function selectDraft(id) {
  await run(async () => {
    draft.value = id ? await api(`/drafts/${id}`) : null;
  });
}
async function newDraft(title) {
  await run(async () => {
    draft.value = await api("/drafts", { title, source: target.value });
    await refreshDrafts();
    notice.value =
      "Draft created. Edits are saved locally until you apply them.";
  });
}
async function edit(record) {
  await run(async () => {
    if (draft.value && draft.value.source !== target.value)
      throw new Error(
        "The selected draft belongs to another source target. Choose a matching draft or create a new one in Changes.",
      );
    const data =
      record.mode === "insert"
        ? { row: null, impact: null }
        : await api(
            `/targets/${target.value}/record/${record.table}?key=${encodeURIComponent(JSON.stringify(record.key))}`,
          );
    const staged = draft.value?.changes.find(
      (c) =>
        c.table === record.table &&
        JSON.stringify(c.key) === JSON.stringify(record.key),
    );
    if (staged && (!staged.before || !staged.after))
      throw new Error(
        "Remove the staged add/remove operation before editing this row again.",
      );
    editor.value = { ...record, ...data, row: staged?.after ?? data.row };
  });
}
async function stage(values) {
  if (saving.value) return;
  saving.value = true;
  await run(async () => {
    if (!draft.value) {
      draft.value = await api("/drafts", {
        title: `NPC edits ${new Date().toISOString().slice(0, 10)}`,
        source: target.value,
      });
    }
    draft.value = await api(`/drafts/${draft.value.id}/changes`, {
      ...values,
      revision: draft.value.revision,
    });
    await refreshDrafts();
    editor.value = null;
    notice.value = "Edit staged. The database has not been changed.";
  });
  saving.value = false;
}
async function updated(value) {
  draft.value = value;
  await refreshDrafts();
}
function applied() {
  refreshKey.value++;
  notice.value =
    "Database transaction recorded. Follow the activation steps and verify in game.";
}
onMounted(() =>
  run(async () => {
    meta.value = await api("/meta");
    await refreshDrafts();
    target.value = meta.value.targets[0]?.id ?? "";
  }),
);
watch(target, () => {
  editor.value = null;
  connect();
});
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <a href="/" class="brand"
        ><span class="brand-mark">N</span
        ><span>Nightcap<small>NPC ADMIN</small></span></a
      >
      <div class="nav-caption">WORKSPACE</div>
      <nav aria-label="Main navigation">
        <button :class="{ active: page === 'browse' }" @click="page = 'browse'">
          NPC explorer <span>01</span>
        </button>
        <button
          :class="{ active: page === 'changes' }"
          @click="page = 'changes'"
        >
          Changes <span>{{ draft?.changes.length ?? 0 }}</span>
        </button>
        <button
          :class="{ active: page === 'history' }"
          @click="page = 'history'"
        >
          Deployment history <span>03</span>
        </button>
      </nav>
      <div class="sidebar-note">
        <strong>A place for deliberate edits.</strong>
        <p>
          Browse → stage → review → apply.<br />Each server change keeps a
          rollback record.
        </p>
      </div>
      <div class="local-badge">
        <span class="status-dot"></span> Runs on your computer
      </div>
    </aside>
    <div class="main-shell">
      <header class="topbar">
        <div>
          <span class="eyebrow">CONTENT OPERATIONS</span>
          <h1>
            {{
              page === "browse"
                ? "NPC explorer"
                : page === "changes"
                  ? "Change workbench"
                  : "Deployment history"
            }}
          </h1>
        </div>
        <div class="target-picker">
          <label for="target">Browse target</label
          ><select
            id="target"
            v-model="target"
            :disabled="!meta?.targets.length"
          >
            <option v-if="!meta?.targets.length" value="">
              No targets configured
            </option>
            <option v-for="t in meta?.targets" :key="t.id" :value="t.id">
              {{ t.label }}{{ t.production ? " · PRODUCTION" : "" }}
            </option></select
          ><span :class="['connection', { good: connected }]">{{
            connecting ? "Connecting…" : connected ? "Connected" : "Offline"
          }}</span
          ><button
            class="quiet"
            @click="connect"
            :disabled="connecting || !target"
          >
            Retry
          </button>
        </div>
      </header>
      <div v-if="error" class="message error" role="alert">
        {{ error
        }}<button aria-label="Dismiss error" @click="error = ''">×</button>
      </div>
      <div v-if="notice" class="message" role="status">
        {{ notice
        }}<button aria-label="Dismiss notice" @click="notice = ''">×</button>
      </div>
      <main>
        <section v-if="meta && !meta.configured" class="setup panel">
          <span class="eyebrow">FIRST RUN</span>
          <h2>Connect your content database</h2>
          <p>
            Add named targets in <code>config.local.json</code>, then restart
            this app. The example configuration includes local Docker on port
            3307 and a hosted-server SSH tunnel on port 3308.
          </p>
          <ol>
            <li>
              Copy <code>config.example.json</code> to
              <code>config.local.json</code>.
            </li>
            <li>
              Enter your database credentials locally and keep only the targets
              you use.
            </li>
            <li>
              Run <code>npm run dev</code> from the
              <code>eq-npc-admin</code> folder.
            </li>
          </ol>
          <p>
            Your connection settings stay on this computer and are excluded from
            Git.
          </p>
        </section>
        <template v-else-if="meta">
          <div class="draft-bar">
            <label for="draft">Working draft</label
            ><select
              id="draft"
              :value="draft?.id ?? ''"
              @change="selectDraft($event.target.value)"
            >
              <option value="">New edits will start a draft</option>
              <option v-for="d in drafts" :key="d.id" :value="d.id">
                {{ d.title }} · {{ d.count }} edits · {{ d.source }}
              </option></select
            ><span v-if="draft" class="muted"
              >Revision {{ draft.revision }} · source {{ draft.source }}</span
            ><button class="quiet" @click="page = 'changes'">
              Review changes →
            </button>
          </div>
          <div v-show="page === 'browse'">
            <NpcWorkspace
              :key="`${target}-${refreshKey}`"
              :target="target"
              :connected="connected"
              :changes="draft?.changes ?? []"
              @edit="edit"
              @error="error = $event"
            />
          </div>
          <ChangeReview
            v-if="page === 'changes'"
            :draft="draft"
            :meta="meta"
            :target="target"
            @create="newDraft"
            @updated="updated"
            @error="error = $event"
            @notice="notice = $event"
            @applied="applied"
          />
          <HistoryView
            v-if="page === 'history'"
            :meta="meta"
            @error="error = $event"
            @applied="applied"
          />
        </template>
        <div v-else class="empty" role="status">Loading your workspace…</div>
      </main>
    </div>
    <RecordEditor
      v-if="editor"
      :key="JSON.stringify(editor.key) + editor.table"
      :record="editor"
      :schema="meta.tables[editor.table]"
      :target="target"
      :busy="saving"
      :external-error="error"
      @close="editor = null"
      @stage="stage"
      @error="error = $event"
    />
  </div>
</template>

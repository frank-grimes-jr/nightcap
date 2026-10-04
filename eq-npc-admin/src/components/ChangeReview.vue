<script setup>
import { ref, watch, computed } from "vue";
import { api, label } from "../api.js";
import DeployPreview from "./DeployPreview.vue";
const props = defineProps({ draft: Object, meta: Object, target: String });
const emit = defineEmits(["create", "updated", "error", "notice", "applied"]);
const title = ref(""),
  deployTarget = ref(props.target),
  preview = ref(null),
  busy = ref(false),
  published = ref(null),
  importText = ref("");
const targetProfile = computed(() =>
  props.meta.targets.find((t) => t.id === deployTarget.value),
);
watch(
  () => [props.draft?.id, props.draft?.revision, deployTarget.value],
  () => {
    preview.value = null;
    published.value = null;
  },
);
const fields = (change) =>
  Object.keys(change.after ?? change.before).filter(
    (k) => String(change.before?.[k]) !== String(change.after?.[k]),
  );
const displayValue = (row, field) =>
  row === null
    ? "—"
    : row[field] === null
      ? "NULL"
      : row[field] === ""
        ? "(empty)"
        : row[field];
async function run(fn) {
  busy.value = true;
  try {
    await fn();
  } catch (e) {
    emit("error", e.message);
  } finally {
    busy.value = false;
  }
}
const body = () => ({
  revision: props.draft.revision,
  target: deployTarget.value,
});
const remove = (c) =>
  run(async () =>
    emit(
      "updated",
      await api(`/drafts/${props.draft.id}/remove-change`, {
        ...body(),
        table: c.table,
        key: c.key,
      }),
    ),
  );
const preflight = () =>
  run(async () => {
    preview.value = await api(`/drafts/${props.draft.id}/preview`, body());
  });
const publish = () =>
  run(async () => {
    published.value = await api(`/drafts/${props.draft.id}/publish`, body());
    emit(
      "notice",
      "Content branch pushed and verified. Server deployment is separate.",
    );
  });
const apply = (confirmation) =>
  run(async () => {
    await api(`/drafts/${props.draft.id}/apply`, {
      ...body(),
      ...confirmation,
    });
    preview.value = null;
    emit("applied");
  });
const importDraft = () =>
  run(async () => {
    const draft = JSON.parse(importText.value);
    emit("updated", await api("/import", { draft, source: props.target }));
    importText.value = "";
  });
</script>
<template>
  <div class="review-layout">
    <section class="panel review-changes">
      <div class="section-head">
        <div>
          <span class="eyebrow">LOCAL DRAFT</span>
          <h2>{{ draft?.title ?? "Start a change set" }}</h2>
        </div>
        <span class="tag">{{ draft?.changes.length ?? 0 }} records</span>
      </div>
      <form
        class="new-draft"
        @submit.prevent="
          emit('create', title);
          title = '';
        "
      >
        <label for="draft-title">Create a new draft</label>
        <div class="inline">
          <input
            id="draft-title"
            v-model="title"
            required
            maxlength="120"
            placeholder="Move tunnel residents, tune named loot…"
          /><button type="submit" :disabled="busy || !target">Create</button>
        </div>
      </form>
      <div v-if="!draft?.changes.length" class="empty">
        <h3>Build one reviewable change set</h3>
        <p>
          Stage edits from the NPC explorer. Your draft survives app restarts.
        </p>
      </div>
      <article
        v-for="change in draft?.changes"
        :key="change.table + JSON.stringify(change.key)"
        class="change-record"
      >
        <div class="section-head">
          <h3>
            {{ label(change.table) }}
            <span class="muted">{{
              Object.values(change.key).join(" / ")
            }}</span>
          </h3>
          <div class="inline">
            <span class="tag">{{
              !change.before ? "ADD" : !change.after ? "REMOVE" : "EDIT"
            }}</span
            ><button class="quiet" :disabled="busy" @click="remove(change)">
              Unstage
            </button>
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Field</th>
                <th>Before</th>
                <th>After</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="field in fields(change)" :key="field">
                <td>{{ label(field) }}</td>
                <td class="before">{{ displayValue(change.before, field) }}</td>
                <td class="after">{{ displayValue(change.after, field) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>
      <div v-if="draft" class="export-actions">
        <a :href="`/api/drafts/${draft.id}/export`" class="button" download
          >Export change set</a
        ><a
          :href="`/api/drafts/${draft.id}/sql`"
          class="button"
          target="_blank"
          rel="noopener"
          >View SQL</a
        ><button :disabled="busy || !draft.changes.length" @click="publish">
          Push content branch to GitHub
        </button>
      </div>
      <p v-if="published" class="callout">
        Pushed <code>{{ published.branch }}</code
        ><br />Commit <code>{{ published.commit }}</code
        >. Review this feature branch in your repository before promotion.
      </p>
      <details class="import-section">
        <summary>Import a portable change set</summary>
        <p class="hint">
          Paste exported JSON. The imported copy will use {{ target }} as its
          source profile and will still need target preflight.
        </p>
        <label for="import-json">Change-set JSON</label
        ><textarea id="import-json" v-model="importText" rows="6"></textarea
        ><button
          :disabled="busy || !importText || !target"
          @click="importDraft"
        >
          Import as a new draft
        </button>
      </details>
    </section>
    <aside class="review-target">
      <section class="panel">
        <span class="eyebrow">DELIVERY</span>
        <h2>Choose a destination</h2>
        <p>
          Preview compares the selected server with your draft’s original
          records.
        </p>
        <label for="deploy-target">Apply target</label
        ><select id="deploy-target" v-model="deployTarget">
          <option v-for="t in meta.targets" :key="t.id" :value="t.id">
            {{ t.label }}{{ t.production ? " · PRODUCTION" : "" }}
          </option></select
        ><button
          class="primary full"
          :disabled="busy || !draft?.changes.length || !deployTarget"
          @click="preflight"
        >
          {{ busy ? "Working…" : "Preview server changes" }}
        </button>
        <p class="hint">
          Publishing a Git branch and applying to a server are independent
          actions. Neither promotes gameplay to main.
        </p>
      </section>
      <DeployPreview
        v-if="preview && targetProfile"
        :preview="preview"
        :target="targetProfile"
        :busy="busy"
        @apply="apply"
      />
    </aside>
  </div>
</template>

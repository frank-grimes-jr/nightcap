<script setup>
import { onMounted, ref, computed } from "vue";
import { api } from "../api.js";
import DeployPreview from "./DeployPreview.vue";
const props = defineProps({ meta: Object });
const emit = defineEmits(["error", "applied"]);
const receipts = ref([]),
  busy = ref(false),
  selected = ref(null),
  preview = ref(null);
const targetProfile = computed(() =>
  props.meta.targets.find((t) => t.id === selected.value?.target),
);
const canRollback = (receipt) =>
  receipt.status === "applied" &&
  receipt.direction === "apply" &&
  !receipts.value.some(
    (r) =>
      r.direction === "rollback" &&
      r.status === "applied" &&
      r.target === receipt.target &&
      r.draftId === receipt.draftId &&
      r.revision === receipt.revision,
  );
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
const refresh = () =>
  run(async () => {
    receipts.value = await api("/receipts");
  });
const rollbackPreview = (receipt) =>
  run(async () => {
    selected.value = receipt;
    preview.value = await api(`/receipts/${receipt.id}/preview-rollback`, {});
  });
const rollback = (confirmation) =>
  run(async () => {
    await api(`/receipts/${selected.value.id}/rollback`, confirmation);
    preview.value = null;
    receipts.value = await api("/receipts");
    emit("applied");
  });
const recover = (receipt) =>
  run(async () => {
    await api(`/receipts/${receipt.id}/recover`, {});
    receipts.value = await api("/receipts");
  });
onMounted(refresh);
</script>
<template>
  <div class="history-layout">
    <section class="panel">
      <div class="section-head">
        <div>
          <span class="eyebrow">AUDIT TRAIL</span>
          <h2>Server transactions</h2>
        </div>
        <button :disabled="busy" @click="refresh">Refresh</button>
      </div>
      <p>
        Each attempt records the target, draft revision and outcome. Rollback
        checks for intervening edits before restoring data.
      </p>
      <div v-if="!receipts.length" class="empty">
        <h3>No deployments yet</h3>
        <p>Applied changes and rollback attempts will appear here.</p>
      </div>
      <article v-for="receipt in receipts" :key="receipt.id" class="receipt">
        <div class="section-head">
          <h3>{{ receipt.title }}</h3>
          <span class="tag"
            >{{ receipt.direction }} · {{ receipt.status }}</span
          >
        </div>
        <p>
          {{ receipt.target }} · revision {{ receipt.revision }} ·
          {{ new Date(receipt.startedAt).toLocaleString() }}
        </p>
        <small>{{ receipt.id }}</small>
        <p v-if="receipt.message">{{ receipt.message }}</p>
        <ol v-if="receipt.status === 'applied'">
          <li v-for="step in receipt.activation" :key="step">{{ step }}</li>
        </ol>
        <button
          v-if="canRollback(receipt)"
          :disabled="busy"
          @click="rollbackPreview(receipt)"
        >
          Preview rollback</button
        ><button
          v-if="['prepared', 'uncertain'].includes(receipt.status)"
          :disabled="busy"
          @click="recover(receipt)"
        >
          Recover outcome from database ledger
        </button>
      </article>
    </section>
    <DeployPreview
      v-if="preview && targetProfile"
      :preview="preview"
      :target="targetProfile"
      :busy="busy"
      rollback
      @apply="rollback"
    />
  </div>
</template>

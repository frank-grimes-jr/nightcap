<script setup>
import { ref, watch } from "vue";
const props = defineProps({
  preview: Object,
  target: Object,
  busy: Boolean,
  rollback: Boolean,
});
const emit = defineEmits(["apply"]);
const confirmation = ref(""),
  maintenance = ref(false);
watch(
  () => props.preview?.hash,
  () => {
    confirmation.value = "";
    maintenance.value = false;
  },
);
</script>
<template>
  <section class="panel deploy-preview">
    <div class="section-head">
      <div>
        <span class="eyebrow">{{
          rollback ? "ROLLBACK PREVIEW" : "SERVER PREVIEW"
        }}</span>
        <h2>{{ target.label }}</h2>
      </div>
      <span :class="['tag', preview.ready ? 'good' : 'bad']">{{
        preview.ready ? "Ready for review" : "Apply blocked"
      }}</span>
    </div>
    <p v-if="target.production" class="callout">
      This is a production target. Review the affected content and current
      maintenance state.
    </p>
    <div v-for="reason in preview.blocked" :key="reason" class="message error">
      {{ reason }}
    </div>
    <div
      v-for="conflict in preview.conflicts"
      :key="JSON.stringify(conflict.key) + conflict.table"
      class="message error"
    >
      <strong
        >{{ conflict.table }} {{ JSON.stringify(conflict.key) }} has changed on
        this target.</strong
      >
      <p>
        Refresh the source record and rebuild the edit; the app will not
        overwrite it.
      </p>
      <details>
        <summary>Compare snapshots</summary>
        <pre>{{
          JSON.stringify(
            { expected: conflict.expected, actual: conflict.actual },
            null,
            2,
          )
        }}</pre>
      </details>
    </div>
    <h3>Affected content</h3>
    <ul class="impact-list">
      <li v-for="effect in preview.effects" :key="effect.identity">
        <strong>{{ effect.total }} NPC templates</strong> ·
        {{ effect.npcs.map((n) => n.name).join(", ")
        }}{{ effect.total > 30 ? "…" : ""
        }}<small
          >Zones:
          {{
            effect.locations
              .map((z) => `${z.zone} (v${z.version})`)
              .join(", ") || "No database spawns found"
          }}</small
        ><small v-if="effect.globalLoot.length"
          >Global loot:
          {{
            effect.globalLoot
              .map(
                (g) =>
                  `${g.description} (${g.enabled ? "enabled" : "disabled"})`,
              )
              .join(", ")
          }}</small
        >
      </li>
    </ul>
    <p class="hint">
      {{ preview.states.length }} scoped saved-state rows will be removed on
      apply. Corpse state and unrelated spawns are preserved.
    </p>
    <h3>Activation & in-game QA</h3>
    <ol class="activation">
      <li v-for="step in preview.activation" :key="step">{{ step }}</li>
    </ol>
    <form
      @submit.prevent="
        emit('apply', {
          previewHash: preview.hash,
          confirmTarget: confirmation,
          maintenanceConfirmed: maintenance,
        })
      "
      class="apply-form"
    >
      <label v-if="preview.needsMaintenance" class="check"
        ><input v-model="maintenance" type="checkbox" />I have stopped the
        affected zones, including their instances, so they cannot save old
        positions during this change.</label
      >
      <label
        >Type <strong>{{ target.label }}</strong> to confirm the
        destination<input
          v-model="confirmation"
          autocomplete="off"
          :placeholder="target.label"
      /></label>
      <button
        class="primary"
        :disabled="
          busy ||
          !preview.ready ||
          confirmation !== target.label ||
          (preview.needsMaintenance && !maintenance)
        "
      >
        {{
          busy
            ? "Recording transaction…"
            : rollback
              ? "Roll back this deployment"
              : "Apply changes to server"
        }}
      </button>
      <p class="hint">
        A before-image and receipt are saved locally. Database changes are
        atomic; reload and in-game verification follow separately.
      </p>
    </form>
  </section>
</template>

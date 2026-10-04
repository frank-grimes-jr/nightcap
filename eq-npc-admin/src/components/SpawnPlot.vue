<script setup>
import { computed, ref, watch } from "vue";
const props = defineProps({ spawns: Array, changes: Array });
const emit = defineEmits(["edit"]);
const selectedZone = ref("");
const zones = computed(() => [
  ...new Set(props.spawns.map((s) => `${s.zone}:${s.version}`)),
]);
watch(
  zones,
  (value) => {
    if (!value.includes(selectedZone.value))
      selectedZone.value = value[0] ?? "";
  },
  { immediate: true },
);
const points = computed(() =>
  props.spawns
    .filter((s) => `${s.zone}:${s.version}` === selectedZone.value)
    .map((s) => ({
      before: s,
      after:
        props.changes.find((c) => c.table === "spawn2" && c.key.id === s.id)
          ?.after ?? s,
    })),
);
const bounds = computed(() => {
  const all = points.value.flatMap((p) => [p.before, p.after]);
  const xs = all.map((p) => Number(p.x)),
    ys = all.map((p) => Number(p.y));
  return {
    x: Math.min(...xs) - 25,
    y: Math.min(...ys) - 25,
    width: Math.max(50, Math.max(...ys) - Math.min(...ys) + 50),
    height: Math.max(50, Math.max(...xs) - Math.min(...xs) + 50),
  };
});
const cx = (p) =>
  560 - ((Number(p.y) - bounds.value.y) / bounds.value.width) * 520;
const cy = (p) =>
  220 - ((Number(p.x) - bounds.value.x) / bounds.value.height) * 190;
</script>
<template>
  <section v-if="spawns.length" class="spawn-plot">
    <div class="section-head">
      <h3>Placement overview</h3>
      <label
        >Zone / version
        <select v-model="selectedZone">
          <option v-for="zone in zones" :key="zone">{{ zone }}</option>
        </select></label
      >
    </div>
    <svg
      viewBox="0 0 600 250"
      role="img"
      aria-label="Overhead spawn coordinates. Select a spawn marker to edit it."
    >
      <defs>
        <pattern id="grid" width="30" height="25" patternUnits="userSpaceOnUse">
          <path
            d="M 30 0 L 0 0 0 25"
            fill="none"
            stroke="currentColor"
            stroke-width="0.5"
          />
        </pattern>
      </defs>
      <rect width="600" height="250" fill="url(#grid)" class="plot-grid" />
      <text x="12" y="20" class="plot-label">N · +X</text>
      <text x="500" y="240" class="plot-label">E · −Y</text>
      <g
        v-for="p in points"
        :key="p.before.id"
        tabindex="0"
        role="button"
        :aria-label="`Edit spawn ${p.before.id}`"
        @click="emit('edit', p.before)"
        @keydown.enter="emit('edit', p.before)"
        @keydown.space.prevent="emit('edit', p.before)"
      >
        <line
          v-if="p.after !== p.before"
          :x1="cx(p.before)"
          :y1="cy(p.before)"
          :x2="cx(p.after)"
          :y2="cy(p.after)"
          class="plot-move"
        />
        <circle
          :cx="cx(p.before)"
          :cy="cy(p.before)"
          r="7"
          class="plot-original"
        />
        <circle
          v-if="p.after !== p.before"
          :cx="cx(p.after)"
          :cy="cy(p.after)"
          r="7"
          class="plot-proposed"
        />
        <text :x="cx(p.after) + 11" :y="cy(p.after) - 9" class="plot-label">
          #{{ p.before.id }}
        </text>
        <title>X {{ p.after.x }}, Y {{ p.after.y }}, Z {{ p.after.z }}</title>
      </g>
    </svg>
    <p class="hint">
      Schematic coordinates, without terrain. White = current; amber = staged.
      Check ground height and pathing in game.
    </p>
  </section>
</template>

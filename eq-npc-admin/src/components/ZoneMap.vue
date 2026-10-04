<script setup>
import { computed, ref, onMounted, onBeforeUnmount, watch } from "vue";
import { worldToMap, project, fitView, zoomView, clipHeight } from "../map.js";
const props = defineProps({
  map: Object,
  pairs: Array,
  minimum: Number,
  maximum: Number,
  layers: Array,
  labels: Boolean,
  selected: [Number, String],
  npcName: String,
});
const emit = defineEmits(["select"]);
const surface = ref(null),
  width = ref(600),
  height = 400,
  view = ref({ x: 0, y: 0, scale: 1 });
let observer, drag;
const inHeight = (z) =>
  Number(z) >= props.minimum && Number(z) <= props.maximum;
const lines = computed(() =>
  (props.map?.lines ?? [])
    .filter((l) => props.layers.includes(l[6]))
    .map((l) => clipHeight(l, props.minimum, props.maximum))
    .filter(Boolean),
);
const outline = computed(() =>
  lines.value.map((l) => `M${l[0]},${l[1]}L${l[3]},${l[4]}`).join(""),
);
const transform = computed(
  () =>
    `translate(${width.value / 2 - view.value.x * view.value.scale} ${height / 2 - view.value.y * view.value.scale}) scale(${view.value.scale})`,
);
const screen = (p) => project(p, view.value, width.value, height);
const visible = ([x, y]) =>
  x >= 16 && x <= width.value - 16 && y >= 18 && y <= height - 18;
const markers = computed(() =>
  props.pairs.flatMap((pair) => {
    const list = [{ row: pair.before, kind: "current" }];
    if (pair.after !== pair.before)
      list.push({ row: pair.after, kind: "staged" });
    return list
      .filter((p) => inHeight(p.row.z))
      .map((p) => ({
        ...p,
        point: screen(worldToMap(p.row)),
        id: pair.before.id,
      }))
      .filter((p) => visible(p.point));
  }),
);
const connectors = computed(() =>
  props.pairs
    .filter((p) => p.before !== p.after)
    .map((p) =>
      clipHeight(
        [...worldToMap(p.before), ...worldToMap(p.after), 0],
        props.minimum,
        props.maximum,
      ),
    )
    .filter(Boolean)
    .map((l) => ({ a: screen(l.slice(0, 3)), b: screen(l.slice(3, 6)) })),
);
const mapLabels = computed(() =>
  props.labels
    ? (props.map?.labels ?? [])
        .filter((l) => props.layers.includes(l.layer) && inHeight(l.z))
        .map((l) => ({ ...l, point: screen([l.x, l.y]) }))
        .filter((l) => visible(l.point))
        .slice(0, 150)
    : [],
);
const scaleUnits = computed(() => {
  const desired = 90 / view.value.scale;
  const power = 10 ** Math.floor(Math.log10(desired));
  return (
    [1, 2, 5]
      .map((n) => n * power)
      .filter((n) => n <= desired)
      .at(-1) ?? power
  );
});
function fit(spawnsOnly = false) {
  const p = props.pairs
    .flatMap((p) => [p.before, p.after])
    .filter((p) => inHeight(p.z))
    .map(worldToMap);
  if (!spawnsOnly)
    for (const l of lines.value) p.push(l.slice(0, 3), l.slice(3, 6));
  view.value = fitView(p, width.value, height);
}
function zoom(factor, x = width.value / 2, y = height / 2) {
  view.value = zoomView(view.value, factor, x, y, width.value, height);
}
function wheel(e) {
  e.preventDefault();
  const r = surface.value.getBoundingClientRect();
  zoom(e.deltaY < 0 ? 1.2 : 1 / 1.2, e.clientX - r.left, e.clientY - r.top);
}
function down(e) {
  if (e.button !== 0 || e.target.closest("button")) return;
  drag = {
    id: e.pointerId,
    x: e.clientX,
    y: e.clientY,
    view: { ...view.value },
  };
  surface.value.setPointerCapture(e.pointerId);
}
function move(e) {
  if (!drag || drag.id !== e.pointerId) return;
  view.value = {
    ...drag.view,
    x: drag.view.x - (e.clientX - drag.x) / drag.view.scale,
    y: drag.view.y - (e.clientY - drag.y) / drag.view.scale,
  };
}
function stop() {
  drag = null;
}
function key(e) {
  if (e.target !== surface.value) return;
  const d = {
    ArrowLeft: [-1, 0],
    ArrowRight: [1, 0],
    ArrowUp: [0, -1],
    ArrowDown: [0, 1],
  }[e.key];
  if (d) {
    e.preventDefault();
    view.value = {
      ...view.value,
      x: view.value.x + (d[0] * 80) / view.value.scale,
      y: view.value.y + (d[1] * 80) / view.value.scale,
    };
  }
  if (e.key === "+" || e.key === "=") {
    e.preventDefault();
    zoom(1.3);
  }
  if (e.key === "-") {
    e.preventDefault();
    zoom(1 / 1.3);
  }
}
watch(
  () => props.map,
  () => fit(),
);
onMounted(() => {
  width.value = surface.value.clientWidth;
  fit();
  observer = new ResizeObserver(() => {
    width.value = surface.value?.clientWidth ?? 600;
  });
  observer.observe(surface.value);
});
onBeforeUnmount(() => observer?.disconnect());
</script>
<template>
  <div class="map-toolbar">
    <div class="inline">
      <button type="button" @click="zoom(1.5)" aria-label="Zoom in">+</button
      ><button type="button" @click="zoom(1 / 1.5)" aria-label="Zoom out">
        −</button
      ><button type="button" @click="fit()">Fit zone</button
      ><button type="button" @click="fit(true)">Fit spawns</button>
    </div>
    <span class="hint">Drag to pan · scroll to zoom · arrow keys to pan</span>
  </div>
  <div
    ref="surface"
    class="zone-map"
    tabindex="0"
    role="region"
    aria-label="Interactive NPC location map"
    @wheel="wheel"
    @pointerdown="down"
    @pointermove="move"
    @pointerup="stop"
    @pointercancel="stop"
    @lostpointercapture="stop"
    @keydown="key"
  >
    <svg
      :viewBox="`0 0 ${width} ${height}`"
      role="img"
      aria-label="Zone outlines and configured spawn locations; north is up and east is right"
    >
      <g :transform="transform"><path :d="outline" class="zone-outline" /></g>
      <line
        v-for="(c, i) in connectors"
        :key="i"
        :x1="c.a[0]"
        :y1="c.a[1]"
        :x2="c.b[0]"
        :y2="c.b[1]"
        class="map-connector"
      />
      <text
        v-for="(l, i) in mapLabels"
        :key="i"
        :x="l.point[0]"
        :y="l.point[1]"
        class="map-text"
        :text-anchor="l.point[0] > width * 0.7 ? 'end' : 'start'"
      >
        {{ l.text }}
      </text>
      <text x="12" y="22" class="map-text">N ↑</text>
      <path :d="`M12 369v6h${scaleUnits * view.scale}v-6`" class="map-scale" />
      <text x="12" y="393" class="map-text">{{ scaleUnits }} zone units</text>
    </svg>
    <button
      v-for="m in markers"
      :key="`${m.id}:${m.kind}`"
      type="button"
      class="spawn-marker"
      :class="[m.kind, { chosen: String(selected) === String(m.id) }]"
      :style="{ left: `${m.point[0]}px`, top: `${m.point[1]}px` }"
      :aria-label="`${npcName} spawn ${m.id}, ${m.kind}, X ${m.row.x}, Y ${m.row.y}, Z ${m.row.z}`"
      :aria-pressed="String(selected) === String(m.id)"
      @click="emit('select', m.id)"
    >
      <span aria-hidden="true"></span>
    </button>
  </div>
  <div class="map-legend">
    <span><i class="current-key"></i>Current spawn</span
    ><span><i class="staged-key"></i>Staged position</span
    ><span class="hint">{{ markers.length }} visible markers</span>
  </div>
</template>
<style scoped>
.map-toolbar,
.map-legend {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  justify-content: space-between;
  margin: 12px 0;
}
.map-toolbar .hint {
  margin: 0;
}
.zone-map {
  position: relative;
  width: 100%;
  height: 400px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 6px;
  overflow: hidden;
  touch-action: none;
  cursor: grab;
}
.zone-map:active {
  cursor: grabbing;
}
.zone-map svg {
  width: 100%;
  height: 400px;
  display: block;
}
.zone-outline {
  fill: none;
  stroke: var(--muted);
  stroke-width: 1;
  vector-effect: non-scaling-stroke;
  opacity: 0.7;
}
.map-text {
  font:
    12px "Segoe UI",
    sans-serif;
  fill: var(--ink);
  stroke: var(--paper);
  stroke-width: 3;
  paint-order: stroke;
  stroke-linejoin: round;
}
.map-scale {
  fill: none;
  stroke: var(--ink);
  stroke-width: 1;
}
.map-connector {
  stroke: var(--amber);
  stroke-width: 2;
  stroke-dasharray: 5 4;
}
.zone-map .spawn-marker {
  position: absolute;
  transform: translate(-50%, -50%);
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  min-height: 0;
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
  cursor: pointer;
}
.spawn-marker span,
.current-key {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid var(--accent);
  background: var(--paper);
  border-radius: 50%;
}
.spawn-marker.staged span,
.staged-key {
  display: inline-block;
  width: 11px;
  height: 11px;
  background: var(--amber);
  border: 1px solid var(--paper);
  border-radius: 0;
  transform: rotate(45deg);
}
.spawn-marker.chosen span {
  outline: 2px solid var(--ink);
  outline-offset: 3px;
}
.spawn-marker:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.map-legend {
  justify-content: flex-start;
  font-size: 12px;
}
.map-legend span {
  display: flex;
  align-items: center;
  gap: 8px;
}
@media (pointer: coarse) {
  .zone-map .spawn-marker {
    width: 44px;
    height: 44px;
  }
}
</style>

<script setup>
import { ref, shallowRef, computed, watch, onBeforeUnmount } from "vue";
import { api } from "../api.js";
import { spawnPairs } from "../map.js";
import ZoneMap from "./ZoneMap.vue";
const props = defineProps({
  spawns: Array,
  changes: Array,
  target: String,
  npcName: String,
});
const emit = defineEmits(["edit"]);
const selectedZone = ref(""),
  selectedId = ref(""),
  map = shallowRef(null),
  loading = ref(false),
  error = ref("");
const sliced = ref(false),
  minZ = ref(-100),
  maxZ = ref(100),
  labels = ref(false),
  layers = ref([0, 1, 2, 3]);
let sequence = 0;
const zones = computed(() => [
  ...new Set(props.spawns.map((s) => `${s.zone}:${s.version}`)),
]);
const pairs = computed(() =>
  spawnPairs(props.spawns, props.changes, selectedZone.value),
);
const selected = computed(() =>
  pairs.value.find((p) => String(p.before.id) === String(selectedId.value)),
);
const minimum = computed(() => (sliced.value ? Number(minZ.value) : -Infinity));
const maximum = computed(() => (sliced.value ? Number(maxZ.value) : Infinity));
const availableLayers = computed(() =>
  [
    ...new Set([
      ...(map.value?.lines ?? []).map((l) => l[6]),
      ...(map.value?.labels ?? []).map((l) => l.layer),
    ]),
  ].sort(),
);
const inSlice = (z) => z >= minimum.value && z <= maximum.value;
const hiddenSpawns = computed(
  () =>
    pairs.value.filter((p) => !inSlice(p.before.z) && !inSlice(p.after.z))
      .length,
);
function aroundSpawn() {
  const z = Number(selected.value?.after.z ?? pairs.value[0]?.after.z ?? 0);
  minZ.value = Math.floor(z - 20);
  maxZ.value = Math.ceil(z + 20);
  sliced.value = true;
}
async function load() {
  const request = ++sequence;
  map.value = null;
  error.value = "";
  loading.value = true;
  layers.value = [0, 1, 2, 3];
  sliced.value = false;
  const [zone, version] = selectedZone.value.split(":");
  if (!zone) {
    loading.value = false;
    return;
  }
  try {
    const value = await api(
      `/targets/${props.target}/maps/${encodeURIComponent(zone)}?version=${encodeURIComponent(version)}`,
    );
    if (request === sequence) map.value = value;
  } catch (e) {
    if (request === sequence) error.value = e.message;
  } finally {
    if (request === sequence) loading.value = false;
  }
}
watch(
  zones,
  (value) => {
    if (!value.includes(selectedZone.value))
      selectedZone.value = value[0] ?? "";
  },
  { immediate: true },
);
watch(
  pairs,
  (value) => {
    if (!value.some((p) => String(p.before.id) === String(selectedId.value)))
      selectedId.value = value[0]?.before.id ?? "";
  },
  { immediate: true },
);
watch([selectedZone, () => props.target], load, { immediate: true });
onBeforeUnmount(() => sequence++);
</script>
<template>
  <section v-if="spawns.length" class="spawn-map-panel">
    <div class="section-head">
      <h3>Zone map</h3>
      <label
        >Zone / version<select v-model="selectedZone">
          <option v-for="zone in zones" :key="zone">{{ zone }}</option>
        </select></label
      >
    </div>
    <p v-if="loading" role="status" class="hint">Loading client map…</p>
    <p v-else-if="error" role="status" class="callout">
      Map unavailable: {{ error }}
      <button type="button" @click="load">Retry map</button>
    </p>
    <p v-else-if="!map?.available" role="status" class="callout">
      {{ map?.reason }} Showing spawn coordinates without zone outlines.
    </p>
    <p v-else class="hint">
      Client map: {{ map.files.join(" + ")
      }}<span v-if="map.invalid">
        · {{ map.invalid }} malformed records skipped</span
      >
    </p>
    <div class="map-options">
      <label class="check"
        ><input
          v-model="labels"
          type="checkbox"
          :disabled="!map?.available"
        />Map labels</label
      >
      <label v-for="layer in availableLayers" :key="layer" class="check"
        ><input v-model="layers" type="checkbox" :value="layer" />Layer
        {{ layer }}</label
      >
      <label class="check"
        ><input v-model="sliced" type="checkbox" />Limit height</label
      >
      <button type="button" @click="aroundSpawn">
        Height near selected spawn
      </button>
    </div>
    <div v-if="sliced" class="map-options height-inputs">
      <label>Minimum Z<input v-model="minZ" type="number" step="1" /></label
      ><label>Maximum Z<input v-model="maxZ" type="number" step="1" /></label
      ><span v-if="minimum > maximum" class="error" role="alert"
        >Minimum Z must not exceed maximum Z.</span
      ><span v-else class="hint"
        >{{ hiddenSpawns }} spawns outside height range</span
      >
    </div>
    <ZoneMap
      :key="`${target}:${selectedZone}`"
      :map="map"
      :pairs="pairs"
      :minimum="minimum"
      :maximum="maximum"
      :layers="layers"
      :labels="labels"
      :selected="selectedId"
      :npc-name="npcName"
      @select="selectedId = $event"
    />
    <div v-if="selected" class="map-selection">
      <label
        >Selected spawn<select v-model="selectedId">
          <option v-for="p in pairs" :key="p.before.id" :value="p.before.id">
            #{{ p.before.id }} · {{ npcName }}
          </option>
        </select></label
      >
      <div aria-live="polite">
        <strong>{{ npcName }}</strong
        ><small
          >Current /loc: {{ selected.before.y }}, {{ selected.before.x }},
          {{ selected.before.z }}</small
        ><small v-if="selected.after !== selected.before"
          >Staged /loc: {{ selected.after.y }}, {{ selected.after.x }},
          {{ selected.after.z }}</small
        >
      </div>
      <button type="button" @click="emit('edit', selected.before)">
        Move / edit selected spawn
      </button>
    </div>
    <p class="hint">
      Configured spawn positions, not live roaming NPCs. Client outlines may
      differ by era; verify the floor and ground height in game. Moving a marker
      uses the location editor and draft review.
    </p>
  </section>
</template>
<style scoped>
.spawn-map-panel {
  padding-bottom: 16px;
  min-width: 0;
}
.spawn-map-panel select {
  max-width: 100%;
}
.map-options {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin: 12px 0;
}
.map-options .check {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
}
.height-inputs input {
  width: 120px;
}
.map-selection {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-top: 1px solid var(--line);
}
.map-selection label {
  min-width: 0;
  max-width: 100%;
}
.map-selection small {
  display: block;
  overflow-wrap: anywhere;
}
.map-selection > div {
  flex: 1;
  min-width: 180px;
}
</style>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { api, label } from "../api.js";
const props = defineProps({
  record: Object,
  schema: Object,
  target: String,
  busy: Boolean,
  externalError: String,
});
const emit = defineEmits(["close", "stage", "error"]);
const dialog = ref(null),
  location = ref(""),
  itemQuery = ref(""),
  itemResults = ref([]),
  error = ref("");
const key = reactive({ ...props.record.key });
const fields = computed(() =>
  (props.record.fields ?? Object.keys(props.schema.fields)).filter(
    (f) =>
      props.record.mode === "insert" ||
      Object.hasOwn(props.record.row ?? {}, f),
  ),
);
const values = reactive(
  Object.fromEntries(
    fields.value.map((f) => [
      f,
      props.record.row?.[f] ??
        props.record.defaults?.[f] ??
        (props.schema.fields[f].type === "number" ? 0 : ""),
    ]),
  ),
);
const insert = props.record.mode === "insert";
const hasItem =
  props.record.table === "lootdrop_entries" ||
  props.record.table === "merchantlist";
const patch = computed(() =>
  Object.fromEntries(
    fields.value
      .filter(
        (f) =>
          insert ||
          String(values[f]) !==
            String(
              props.record.row?.[f] ??
                (props.schema.fields[f].type === "number" ? 0 : ""),
            ),
      )
      .map((f) => [f, values[f]]),
  ),
);
const editableKey = insert
  ? {
      lootdrop_entries: "item_id",
      merchantlist: "slot",
      loottable_entries: "lootdrop_id",
    }[props.record.table]
  : null;
onMounted(() => dialog.value.showModal());
async function pasteLocation() {
  try {
    Object.assign(
      values,
      await api("/parse-location", { text: location.value }),
    );
    error.value = "";
  } catch (e) {
    error.value = e.message;
  }
}
async function findItems() {
  try {
    itemResults.value = await api(
      `/targets/${props.target}/items?q=${encodeURIComponent(itemQuery.value)}`,
    );
  } catch (e) {
    error.value = e.message;
  }
}
function chooseItem(item) {
  if (props.record.table === "merchantlist") values.item = item.id;
  else key.item_id = item.id;
  itemResults.value = [];
  itemQuery.value = item.name;
}
function stage(mode = props.record.mode ?? "update") {
  emit("stage", {
    table: props.record.table,
    key: { ...key },
    expected: props.record.row,
    patch: { ...patch.value },
    mode,
  });
}
</script>
<template>
  <dialog ref="dialog" class="editor-dialog" @close="emit('close')">
    <header class="section-head">
      <div>
        <span class="eyebrow"
          >{{ insert ? "ADD RECORD" : "STAGE AN EDIT" }} ·
          {{ label(record.table) }}</span
        >
        <h2>{{ record.title }}</h2>
      </div>
      <button
        class="quiet close"
        aria-label="Close editor"
        @click="dialog.close()"
      >
        ×
      </button>
    </header>
    <div class="editor-content">
      <p v-if="record.impact" class="callout">
        Used by {{ record.impact.total }} NPC template{{
          record.impact.total === 1 ? "" : "s"
        }}{{
          record.impact.globalLoot.length
            ? ` and ${record.impact.globalLoot.length} global loot rule(s)`
            : ""
        }}.<span v-if="record.impact.npcs.length">
          {{ record.impact.npcs.map((n) => n.name).join(", ")
          }}{{ record.impact.total > 30 ? "…" : "" }}</span
        >
      </p>
      <p v-else class="hint">
        Shared-resource impact will be checked before applying this addition.
      </p>
      <div v-if="error" class="message error" role="alert">{{ error }}</div>
      <div v-if="externalError" class="message error" role="alert">
        {{ externalError }}
      </div>
      <form
        v-if="record.table === 'spawn2'"
        @submit.prevent="pasteLocation"
        class="loc-input"
      >
        <label for="paste-loc">Paste in-game /loc · Y, X, Z</label>
        <div class="inline">
          <input
            id="paste-loc"
            v-model="location"
            placeholder="Your Location is -185, -1506, 2"
          /><button type="submit">Use coordinates</button>
        </div>
      </form>
      <form
        v-if="hasItem && (insert || record.table === 'merchantlist')"
        @submit.prevent="findItems"
        class="item-search"
      >
        <label for="item-search">Find an item by name or ID</label>
        <div class="inline">
          <input
            id="item-search"
            v-model="itemQuery"
            maxlength="100"
            placeholder="Rusty Scythe"
          /><button type="submit">Find item</button>
        </div>
        <div class="item-results">
          <button
            v-for="item in itemResults"
            :key="item.id"
            type="button"
            @click="chooseItem(item)"
          >
            {{ item.name }}
            <span
              >#{{ item.id
              }}{{ item.id > 1048575 ? " · beyond RoF2 link limit" : "" }}</span
            >
          </button>
        </div>
      </form>
      <form id="edit-fields" @submit.prevent="stage()">
        <label v-if="editableKey" class="field"
          >{{ label(editableKey)
          }}<input
            v-model.number="key[editableKey]"
            type="number"
            required
            min="1"
            max="2147483647"
            step="1"
        /></label>
        <div class="field-grid">
          <label v-for="field in fields" :key="field" class="field"
            >{{ label(field)
            }}<input
              v-if="schema.fields[field].type === 'number'"
              v-model.number="values[field]"
              type="number"
              required
              :min="schema.fields[field].min"
              :max="schema.fields[field].max"
              :step="schema.fields[field].integer ? 1 : 'any'"
            /><input
              v-else
              v-model="values[field]"
              type="text"
              :maxlength="schema.fields[field].maxLength"
            /><small v-if="!insert"
              >Current:
              {{
                record.row[field] === "" ? "(empty)" : record.row[field]
              }}</small
            ></label
          >
        </div>
      </form>
      <p class="hint">
        Saving stages this record in your local draft. Applying to a server is a
        separate step.
      </p>
    </div>
    <footer class="dialog-footer">
      <button
        v-if="schema.remove && !insert"
        class="danger quiet"
        :disabled="busy"
        @click="stage('delete')"
      >
        Stage removal</button
      ><span class="spacer"></span
      ><button :disabled="busy" @click="dialog.close()">Cancel</button
      ><button
        class="primary"
        type="submit"
        form="edit-fields"
        :disabled="busy || !Object.keys(patch).length"
      >
        {{ busy ? "Saving…" : insert ? "Stage addition" : "Stage changes" }}
      </button>
    </footer>
  </dialog>
</template>

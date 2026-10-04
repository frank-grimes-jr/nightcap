<script setup>
import { ref, watch } from "vue";
import { api } from "../api.js";
import SpawnPlot from "./SpawnPlot.vue";
const props = defineProps({
  target: String,
  connected: Boolean,
  changes: Array,
});
const emit = defineEmits(["edit", "error"]);
const q = ref(""),
  zone = ref(""),
  offset = ref(0),
  zoneList = ref([]),
  results = ref([]),
  detail = ref(null),
  tab = ref("overview"),
  loading = ref(false),
  loadingNpc = ref(false);
let searchSequence = 0,
  detailSequence = 0;
async function search(reset = true) {
  if (!props.connected) return;
  if (reset) offset.value = 0;
  const sequence = ++searchSequence;
  loading.value = true;
  try {
    const value = await api(
      `/targets/${props.target}/npcs?q=${encodeURIComponent(q.value)}&zone=${encodeURIComponent(zone.value)}&offset=${offset.value}`,
    );
    if (sequence === searchSequence) results.value = value;
  } catch (e) {
    emit("error", e.message);
  } finally {
    if (sequence === searchSequence) loading.value = false;
  }
}
async function select(npc) {
  const sequence = ++detailSequence;
  loadingNpc.value = true;
  try {
    const value = await api(`/targets/${props.target}/npcs/${npc.id}`);
    if (sequence === detailSequence) {
      detail.value = value;
      tab.value = "overview";
    }
  } catch (e) {
    emit("error", e.message);
  } finally {
    if (sequence === detailSequence) loadingNpc.value = false;
  }
}
const editSpawn = (s) =>
  emit("edit", {
    table: "spawn2",
    key: { id: s.id },
    title: `Spawn #${s.id} · ${s.zone}`,
    fields: [
      "x",
      "y",
      "z",
      "heading",
      "respawntime",
      "variance",
      "pathgrid",
      "animation",
    ],
  });
const editNpc = (fields) =>
  emit("edit", {
    table: "npc_types",
    key: { id: detail.value.npc.id },
    title: detail.value.npc.name,
    fields,
  });
function addItem(group) {
  emit("edit", {
    table: "lootdrop_entries",
    key: { lootdrop_id: group.lootdrop_id, item_id: 1 },
    mode: "insert",
    title: `Add loot item to ${group.name}`,
    fields: [
      "chance",
      "item_charges",
      "equip_item",
      "multiplier",
      "min_expansion",
      "max_expansion",
    ],
    defaults: {
      chance: 1,
      item_charges: 1,
      equip_item: 0,
      multiplier: 1,
      min_expansion: -1,
      max_expansion: -1,
    },
  });
}
watch(
  () => props.connected,
  async (connected) => {
    if (connected) {
      try {
        zoneList.value = await api(`/targets/${props.target}/zones`);
        await search();
      } catch (e) {
        emit("error", e.message);
      }
    }
  },
  { immediate: true },
);
</script>
<template>
  <div v-if="!connected" class="empty panel">
    <h2>Connect to browse NPCs</h2>
    <p>
      Start the database or SSH tunnel, then use Retry above. Your saved drafts
      remain available in Changes.
    </p>
  </div>
  <div v-else class="explorer">
    <section class="npc-list panel" aria-label="NPC search">
      <form @submit.prevent="search()" class="search-form">
        <label for="npc-query">Find an NPC</label>
        <div class="inline">
          <input
            id="npc-query"
            v-model="q"
            type="search"
            placeholder="Name or NPC ID"
            maxlength="100"
          /><button type="submit" :disabled="loading">Search</button>
        </div>
        <label for="zone">Zone</label
        ><select id="zone" v-model="zone" @change="search()">
          <option value="">All zones</option>
          <option
            v-for="z in zoneList"
            :key="z.short_name"
            :value="z.short_name"
          >
            {{ z.long_name }} · {{ z.short_name }}
          </option>
        </select>
      </form>
      <div class="list-heading">
        <span>{{
          loading ? "Searching…" : `${Math.min(results.length, 100)} results`
        }}</span
        ><span>LEVEL / SPAWNS</span>
      </div>
      <div class="results" :aria-busy="loading">
        <button
          v-for="n in results.slice(0, 100)"
          :key="n.id"
          class="npc-result"
          :class="{ selected: detail?.npc.id === n.id }"
          @click="select(n)"
        >
          <span
            ><strong>{{ n.name.replaceAll("_", " ") || "Unnamed NPC" }}</strong
            ><small
              >#{{ n.id }}{{ n.merchant_id ? " · Merchant" : "" }}</small
            ></span
          ><span class="npc-result-meta"
            >{{ n.level }}<small>{{ n.spawn_count }} locations</small></span
          >
        </button>
        <div v-if="!loading && !results.length" class="empty small">
          No NPCs matched. Try another name or zone.
        </div>
      </div>
      <div class="pagination">
        <button
          :disabled="offset === 0 || loading"
          @click="
            offset -= 100;
            search(false);
          "
        >
          ← Previous</button
        ><span
          >{{ results.length ? offset + 1 : 0 }}–{{
            offset + Math.min(results.length, 100)
          }}</span
        ><button
          :disabled="results.length <= 100 || loading"
          @click="
            offset += 100;
            search(false);
          "
        >
          Next →
        </button>
      </div>
    </section>
    <section class="npc-detail panel" :aria-busy="loadingNpc">
      <div v-if="loadingNpc" class="empty" role="status">
        Loading NPC relationships…
      </div>
      <div v-else-if="!detail" class="empty welcome">
        <span class="eyebrow">YOUR WORLD, WITH CONTEXT</span>
        <h2>Select an NPC to begin</h2>
        <p>
          Inspect its locations, shared loot and merchant stock.<br />Stage
          changes as you work and review them together.
        </p>
        <div class="workflow">
          <span>Find</span><span>Stage</span><span>Review</span
          ><span>Apply</span>
        </div>
      </div>
      <template v-else>
        <div class="npc-heading">
          <div>
            <span class="eyebrow">NPC #{{ detail.npc.id }}</span>
            <h2>{{ detail.npc.name.replaceAll("_", " ") || "Unnamed NPC" }}</h2>
            <p>
              {{ detail.npc.lastname || "No surname" }}
              <span>· Level {{ detail.npc.level }}</span>
            </p>
          </div>
          <span class="tag"
            >{{ detail.spawns.length }} spawn{{
              detail.spawns.length === 1 ? "" : "s"
            }}</span
          >
        </div>
        <div class="tabs" aria-label="NPC sections">
          <button
            v-for="entry in [
              ['overview', 'Details'],
              ['spawns', 'Locations'],
              ['loot', 'Loot'],
              ['merchant', 'Merchant'],
            ]"
            :key="entry[0]"
            :aria-pressed="tab === entry[0]"
            :class="{ active: tab === entry[0] }"
            @click="tab = entry[0]"
          >
            {{ entry[1] }}
          </button>
        </div>
        <div class="detail-body">
          <template v-if="tab === 'overview'">
            <div class="section-head">
              <h3>Identity & appearance</h3>
              <button
                @click="
                  editNpc([
                    'name',
                    'lastname',
                    'level',
                    'maxlevel',
                    'race',
                    'class',
                    'gender',
                    'size',
                    'texture',
                    'helmtexture',
                    'armortint_red',
                    'armortint_green',
                    'armortint_blue',
                    'd_melee_texture1',
                    'd_melee_texture2',
                    'findable',
                    'trackable',
                  ])
                "
              >
                Edit details
              </button>
            </div>
            <dl class="facts">
              <div>
                <dt>Race / class</dt>
                <dd>{{ detail.npc.race }} / {{ detail.npc.class }}</dd>
              </div>
              <div>
                <dt>Gender / size</dt>
                <dd>{{ detail.npc.gender }} / {{ detail.npc.size }}</dd>
              </div>
              <div>
                <dt>Texture / helm</dt>
                <dd>{{ detail.npc.texture }} / {{ detail.npc.helmtexture }}</dd>
              </div>
              <div>
                <dt>Faction</dt>
                <dd>{{ detail.npc.npc_faction_id }}</dd>
              </div>
            </dl>
            <p class="hint">
              Appearance must exist in the client’s loaded models. Changing an
              NPC template affects every spawn using it.
            </p>
            <div class="section-head">
              <h3>Combat & behavior</h3>
              <button
                @click="
                  editNpc([
                    'hp',
                    'mana',
                    'AC',
                    'mindmg',
                    'maxdmg',
                    'attack_count',
                    'attack_delay',
                    'hp_regen_rate',
                    'mana_regen_rate',
                    'aggroradius',
                    'assistradius',
                    'runspeed',
                    'npc_faction_id',
                    'npc_spells_id',
                    'bodytype',
                  ])
                "
              >
                Edit combat
              </button>
            </div>
            <dl class="facts">
              <div>
                <dt>Health</dt>
                <dd>{{ Number(detail.npc.hp).toLocaleString() }}</dd>
              </div>
              <div>
                <dt>Armor class</dt>
                <dd>{{ detail.npc.AC }}</dd>
              </div>
              <div>
                <dt>Damage</dt>
                <dd>{{ detail.npc.mindmg }}–{{ detail.npc.maxdmg }}</dd>
              </div>
              <div>
                <dt>Aggro / assist</dt>
                <dd>
                  {{ detail.npc.aggroradius }} / {{ detail.npc.assistradius }}
                </dd>
              </div>
            </dl>
            <p class="callout">
              Balance against the combined player build: classes, AAs, gear,
              pets and sustain. Combat edits need representative in-game
              encounter QA.
            </p>
          </template>
          <template v-if="tab === 'spawns'">
            <SpawnPlot
              :spawns="detail.spawns"
              :changes="changes"
              @edit="editSpawn"
            />
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Spawn / zone</th>
                    <th>X / Y / Z</th>
                    <th>Heading</th>
                    <th>Respawn</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="s in detail.spawns" :key="s.id">
                    <td>
                      <strong>#{{ s.id }} · {{ s.zone }}</strong
                      ><small
                        >Version {{ s.version }} · group {{ s.spawngroupID }} ·
                        {{ s.spawn_chance }}%</small
                      ><small>{{
                        detail.alternatives
                          .filter((a) => a.spawngroupID === s.spawngroupID)
                          .map((a) => a.name)
                          .join(", ")
                      }}</small>
                    </td>
                    <td class="numeric">{{ s.x }} / {{ s.y }} / {{ s.z }}</td>
                    <td>{{ s.heading }}</td>
                    <td>{{ s.respawntime }}s</td>
                    <td><button @click="editSpawn(s)">Move / edit</button></td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-if="!detail.spawns.length" class="empty small">
              No database spawns. This NPC may be summoned by a quest.
            </p>
          </template>
          <template v-if="tab === 'loot'">
            <div class="section-head">
              <h3>{{ detail.loot?.name ?? "No loot table assigned" }}</h3>
              <div class="inline">
                <button @click="editNpc(['loottable_id'])">Assign table</button
                ><button
                  v-if="detail.loot"
                  @click="
                    emit('edit', {
                      table: 'loottable',
                      key: { id: detail.loot.id },
                      title: detail.loot.name,
                    })
                  "
                >
                  Edit table / cash
                </button>
              </div>
            </div>
            <p class="hint">
              Chance is not always the final drop rate: group probability,
              multipliers, drop limits and guaranteed drops interact. Global
              loot and quest rewards are additional sources.
            </p>
            <div
              v-for="group in detail.lootGroups"
              :key="group.lootdrop_id"
              class="loot-group"
            >
              <div class="section-head">
                <div>
                  <h3>
                    {{ group.name }}
                    <span class="muted">#{{ group.lootdrop_id }}</span>
                  </h3>
                  <p class="hint">
                    {{ group.probability }}% group roll ·
                    {{ group.multiplier }}× · min {{ group.mindrop }} / max
                    {{ group.droplimit || "unlimited" }}
                  </p>
                </div>
                <div class="inline">
                  <button
                    @click="
                      emit('edit', {
                        table: 'loottable_entries',
                        key: {
                          loottable_id: group.loottable_id,
                          lootdrop_id: group.lootdrop_id,
                        },
                        title: group.name,
                      })
                    "
                  >
                    Edit group</button
                  ><button @click="addItem(group)">+ Item</button>
                </div>
              </div>
              <div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Item</th>
                      <th>Chance / weight</th>
                      <th>Charges / multiplier</th>
                      <th>Era</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="item in detail.lootItems.filter(
                        (i) => i.lootdrop_id === group.lootdrop_id,
                      )"
                      :key="`${item.item_id}-${item.item_charges}`"
                    >
                      <td>
                        {{ item.item_name ?? "Missing item"
                        }}<small
                          >#{{ item.item_id
                          }}{{ item.equip_item ? " · NPC equips" : "" }}</small
                        >
                      </td>
                      <td>{{ item.chance }}</td>
                      <td>{{ item.item_charges }} / {{ item.multiplier }}×</td>
                      <td>{{ item.min_expansion }}–{{ item.max_expansion }}</td>
                      <td>
                        <button
                          @click="
                            emit('edit', {
                              table: 'lootdrop_entries',
                              key: {
                                lootdrop_id: item.lootdrop_id,
                                item_id: item.item_id,
                              },
                              title: item.item_name,
                            })
                          "
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <button
              v-if="detail.loot"
              @click="
                emit('edit', {
                  table: 'loottable_entries',
                  key: { loottable_id: detail.loot.id, lootdrop_id: 1 },
                  mode: 'insert',
                  title: 'Add existing loot group',
                  fields: ['probability', 'multiplier', 'droplimit', 'mindrop'],
                  defaults: {
                    probability: 100,
                    multiplier: 1,
                    droplimit: 0,
                    mindrop: 0,
                  },
                })
              "
            >
              + Attach existing loot group
            </button>
          </template>
          <template v-if="tab === 'merchant'">
            <div class="section-head">
              <h3>Merchant #{{ detail.npc.merchant_id || "unassigned" }}</h3>
              <div class="inline">
                <button @click="editNpc(['merchant_id', 'class'])">
                  Assign merchant</button
                ><button
                  v-if="detail.npc.merchant_id"
                  @click="
                    emit('edit', {
                      table: 'merchantlist',
                      key: {
                        merchantid: detail.npc.merchant_id,
                        slot:
                          Math.max(0, ...detail.merchants.map((m) => m.slot)) +
                          1,
                      },
                      mode: 'insert',
                      title: 'Add merchant item',
                      fields: [
                        'item',
                        'level_required',
                        'faction_required',
                        'probability',
                        'min_expansion',
                        'max_expansion',
                      ],
                      defaults: {
                        item: 1,
                        level_required: 0,
                        faction_required: -2000,
                        probability: 100,
                        min_expansion: -1,
                        max_expansion: -1,
                      },
                    })
                  "
                >
                  + Stock item
                </button>
              </div>
            </div>
            <p v-if="detail.npc.class !== 41" class="callout">
              An NPC must be class 41 (Merchant) to open a shop. Assigning a
              merchant ID alone is insufficient.
            </p>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Slot</th>
                    <th>Item</th>
                    <th>Level</th>
                    <th>Era</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="m in detail.merchants" :key="m.slot">
                    <td>{{ m.slot }}</td>
                    <td>
                      {{ m.item_name }}<small>#{{ m.item }}</small>
                    </td>
                    <td>{{ m.level_required }}</td>
                    <td>{{ m.min_expansion }}–{{ m.max_expansion }}</td>
                    <td>
                      <button
                        @click="
                          emit('edit', {
                            table: 'merchantlist',
                            key: { merchantid: m.merchantid, slot: m.slot },
                            title: m.item_name,
                          })
                        "
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="hint">
              Existing curated class-hub stock has its own catalog policy. Era
              expansion requires review and regeneration through the hub
              tooling.
            </p>
          </template>
        </div>
      </template>
    </section>
  </div>
</template>

<template>
  <div class="flex flex-col lg:flex-row min-h-screen">
    <!-- ── Character List ─────────────────────────────────────────── -->
    <div
      class="lg:w-64 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0"
    >
      <div class="p-3 border-b border-gray-800">
        <input
          v-model="search"
          class="input"
          placeholder="Search characters…"
          aria-label="Search characters"
        />
      </div>
      <div class="flex-1 overflow-y-auto">
        <div v-if="loading.chars" class="p-4 text-gray-500 text-sm">
          Loading…
        </div>
        <div
          v-else-if="!filteredChars.length"
          class="p-4 text-gray-600 text-sm"
        >
          No characters found
        </div>
        <button
          v-for="c in filteredChars"
          :key="c.id"
          @click="selectChar(c)"
          class="w-full text-left px-3 py-2.5 border-b border-gray-800 hover:bg-gray-800 transition-colors"
          :class="
            selected?.id === c.id
              ? 'bg-gray-800 border-l-2 border-l-amber-500'
              : ''
          "
        >
          <div class="font-medium text-sm text-gray-100">{{ c.name }}</div>
          <div class="text-xs text-gray-500 mt-0.5">
            Lv {{ c.level }} {{ CLASS_NAMES[c.class] ?? `Class ${c.class}` }} ·
            {{ RACE_NAMES[c.race] ?? `Race ${c.race}` }}
          </div>
        </button>
      </div>
      <div class="p-3 border-t border-gray-800">
        <button class="btn-ghost w-full text-xs" @click="loadChars">
          ↺ Refresh
        </button>
      </div>
    </div>

    <!-- ── GM Panel ───────────────────────────────────────────────── -->
    <div class="flex-1 overflow-y-auto p-6">
      <div
        v-if="!selected"
        class="flex items-center justify-center h-full text-gray-600"
      >
        <div class="text-center">
          <div class="text-4xl mb-3">⚔</div>
          <div>Select a character to begin</div>
        </div>
      </div>

      <template v-else>
        <!-- Header -->
        <div class="mb-6 flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-white">{{ selected.name }}</h1>
            <p class="text-gray-400 text-sm mt-0.5">
              {{ CLASS_NAMES[selected.class] }} ·
              {{ RACE_NAMES[selected.race] }} · Level {{ selected.level }}
              <span v-if="selected.aa_points > 0" class="ml-2 text-amber-400"
                >{{ selected.aa_points }} AA</span
              >
            </p>
          </div>
          <div class="text-xs text-gray-600">ID: {{ selected.id }}</div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <!-- ── Level Boost ──────────────────────────────────────── -->
          <div class="card col-span-2">
            <div class="card-title">Level Boost</div>
            <div class="flex items-end gap-3">
              <div class="flex-1">
                <label class="text-xs text-gray-500 mb-1 block"
                  >Target Expansion</label
                >
                <select v-model="boost.expansionIdx" class="select w-full">
                  <option v-for="(exp, i) in EXPANSIONS" :key="i" :value="i">
                    {{ exp.name }} — Max Level {{ exp.max_level }}
                  </option>
                </select>
              </div>
              <div class="w-28">
                <label class="text-xs text-gray-500 mb-1 block"
                  >Or set level</label
                >
                <input
                  v-model.number="boost.customLevel"
                  type="number"
                  min="1"
                  max="125"
                  class="input"
                  placeholder="Custom"
                />
              </div>
              <button
                class="btn-primary px-5 py-2 text-base font-bold"
                :disabled="loading.boost"
                @click="doBoost"
              >
                {{ loading.boost ? 'Boosting…' : `BOOST → Lv ${boostTarget}` }}
              </button>
            </div>
            <div class="mt-2 text-xs text-gray-600">
              Current level: {{ selected.level }} → Target:
              {{ boostTarget }} (exp reset to 0)
            </div>
          </div>

          <!-- ── Currency ─────────────────────────────────────────── -->
          <div class="card">
            <div class="card-title">Currency</div>
            <div class="grid grid-cols-2 gap-2 mb-3 text-sm">
              <div>
                <span class="text-gray-500">Carried Plat:</span>
                <span class="ml-1 text-amber-300 font-mono">{{
                  (selected.platinum ?? 0).toLocaleString()
                }}</span>
              </div>
              <div>
                <span class="text-gray-500">Bank Plat:</span>
                <span class="ml-1 text-amber-300 font-mono">{{
                  (selected.platinum_bank ?? 0).toLocaleString()
                }}</span>
              </div>
            </div>
            <div class="flex gap-2 flex-wrap">
              <button
                class="btn-green"
                :disabled="loading.currency"
                @click="grantPlat(10000)"
              >
                +10k Plat
              </button>
              <button
                class="btn-green"
                :disabled="loading.currency"
                @click="grantPlat(100000)"
              >
                +100k Plat
              </button>
              <button
                class="btn-green"
                :disabled="loading.currency"
                @click="grantPlat(1000000)"
              >
                +1M Plat
              </button>
              <div class="flex gap-1">
                <input
                  v-model.number="currency.custom"
                  type="number"
                  min="1"
                  class="input w-24"
                  placeholder="Custom"
                />
                <button
                  class="btn-ghost"
                  :disabled="loading.currency || !currency.custom"
                  @click="grantPlat(currency.custom)"
                >
                  Grant
                </button>
              </div>
            </div>
          </div>

          <!-- ── AA Points ─────────────────────────────────────────── -->
          <div class="card">
            <div class="card-title">Alternate Advancement</div>
            <div class="mb-3 text-sm">
              <span class="text-gray-500">Unspent AAs:</span>
              <span class="ml-1 text-blue-300 font-bold font-mono">{{
                (selected.aa_points ?? 0).toLocaleString()
              }}</span>
              <span class="ml-3 text-gray-600"
                >Spent:
                {{ (selected.aa_points_spent ?? 0).toLocaleString() }}</span
              >
            </div>
            <div class="flex gap-2 flex-wrap">
              <button
                class="btn-blue"
                :disabled="loading.aa"
                @click="grantAA(100)"
              >
                +100 AA
              </button>
              <button
                class="btn-blue"
                :disabled="loading.aa"
                @click="grantAA(500)"
              >
                +500 AA
              </button>
              <button
                class="btn-blue"
                :disabled="loading.aa"
                @click="grantAA(2000)"
              >
                +2000 AA
              </button>
              <div class="flex gap-1">
                <input
                  v-model.number="aa.custom"
                  type="number"
                  min="1"
                  class="input w-20"
                  placeholder="Amt"
                />
                <button
                  class="btn-ghost"
                  :disabled="loading.aa || !aa.custom"
                  @click="grantAA(aa.custom)"
                >
                  Grant
                </button>
              </div>
            </div>
          </div>

          <!-- ── Stats ────────────────────────────────────────────── -->
          <div class="card">
            <div class="card-title">Base Stats</div>
            <div class="grid grid-cols-3 gap-2 text-xs">
              <div
                v-for="stat in STATS"
                :key="stat.key"
                class="bg-gray-800 rounded p-2 flex flex-col items-center"
              >
                <span class="text-gray-500 uppercase font-bold">{{
                  stat.label
                }}</span>
                <span class="text-white font-mono text-lg mt-1">{{
                  (selected as any)[stat.key] ?? 0
                }}</span>
              </div>
            </div>
          </div>

          <!-- ── Skills ───────────────────────────────────────────── -->
          <div class="card">
            <div class="card-title">Skills</div>
            <p class="text-gray-500 text-xs mb-3">
              Maximize all combat and tradeskill skills to their cap for the
              character's current class and level.
            </p>
            <button
              class="btn-primary w-full py-2 font-bold"
              :disabled="loading.skills"
              @click="doMaxSkills"
            >
              {{ loading.skills ? 'Maxing Skills…' : 'MAX ALL SKILLS' }}
            </button>
            <div v-if="skillResult" class="mt-2 text-xs text-emerald-400">
              {{ skillResult }}
            </div>
          </div>

          <!-- ── Teleport ──────────────────────────────────────────── -->
          <div class="card col-span-2">
            <div class="card-title">Teleport Character</div>
            <div class="flex gap-3 items-end">
              <div class="flex-1">
                <label class="text-xs text-gray-500 mb-1 block">Zone</label>
                <input
                  v-model="teleport.search"
                  class="input mb-1"
                  placeholder="Search zones…"
                />
                <select
                  v-model="teleport.selectedZone"
                  class="select w-full"
                  size="4"
                  style="height: auto"
                  @change="onZoneSelect"
                >
                  <option v-for="z in filteredZones" :key="z.id" :value="z">
                    {{ z.long_name }} ({{ z.short_name }})
                  </option>
                </select>
              </div>
              <div class="space-y-2 w-44">
                <div>
                  <label class="text-xs text-gray-500 block">Safe X</label>
                  <input
                    v-model.number="teleport.x"
                    type="number"
                    class="input"
                  />
                </div>
                <div>
                  <label class="text-xs text-gray-500 block">Safe Y</label>
                  <input
                    v-model.number="teleport.y"
                    type="number"
                    class="input"
                  />
                </div>
                <div>
                  <label class="text-xs text-gray-500 block">Safe Z</label>
                  <input
                    v-model.number="teleport.z"
                    type="number"
                    class="input"
                  />
                </div>
              </div>
              <button
                class="btn-blue px-6 py-3 font-bold text-base"
                :disabled="loading.teleport || !teleport.selectedZone"
                @click="doTeleport"
              >
                {{ loading.teleport ? 'Moving…' : 'TELEPORT' }}
              </button>
            </div>
            <div
              v-if="teleport.selectedZone"
              class="mt-2 text-xs text-gray-600"
            >
              → {{ teleport.selectedZone.long_name }} ({{
                teleport.selectedZone.short_name
              }}) at {{ teleport.x }}, {{ teleport.y }}, {{ teleport.z }}
            </div>
            <div class="mt-2 text-xs text-yellow-600">
              Character must be offline for teleport to take effect on next
              login.
            </div>
          </div>

          <!-- ── Progression Checklist ────────────────────────────────── -->
          <div class="card col-span-2">
            <div class="flex items-center justify-between mb-3">
              <div class="card-title mb-0">Expansion Progression</div>
              <div class="text-xs text-gray-600">
                {{ totalCleared }}/{{ totalBosses }} targets cleared
                <span
                  v-if="expansionsCleared > 0"
                  class="ml-2 text-emerald-500 font-bold"
                >
                  {{ expansionsCleared }} expansion{{
                    expansionsCleared !== 1 ? 's' : ''
                  }}
                  complete
                </span>
              </div>
            </div>

            <!-- Expansion Tabs -->
            <div class="overflow-x-auto pb-1 mb-3">
              <div class="flex gap-1 min-w-max">
                <button
                  v-for="exp in progBosses"
                  :key="exp.expansion_id"
                  @click="progExpIdx = exp.expansion_id"
                  class="flex flex-col items-center px-2.5 py-1.5 rounded border text-xs transition-all min-w-[54px]"
                  :class="[
                    progExpIdx === exp.expansion_id
                      ? 'bg-amber-600/20 border-amber-500 text-white'
                      : expCleared(exp)
                        ? 'bg-emerald-900/20 border-emerald-700 text-emerald-400'
                        : expStarted(exp)
                          ? 'bg-gray-800 border-gray-600 text-gray-300'
                          : 'bg-gray-900 border-gray-800 text-gray-600 hover:border-gray-700',
                  ]"
                >
                  <span class="font-bold">{{ exp.short }}</span>
                  <span
                    class="font-mono mt-0.5"
                    :class="
                      expCleared(exp) ? 'text-emerald-500' : 'text-gray-600'
                    "
                  >
                    {{ killedInExp(exp) }}/{{ exp.bosses.length }}
                  </span>
                  <span
                    v-if="expCleared(exp)"
                    class="text-emerald-400 text-[10px] leading-none mt-0.5"
                    >✓ CLEAR</span
                  >
                </button>
              </div>
            </div>

            <!-- Selected Expansion Boss List -->
            <div
              v-if="selectedProgExp?.note"
              class="mb-3 text-xs text-amber-700 bg-amber-900/20 border border-amber-800/30 rounded px-3 py-2"
            >
              ⚠ {{ selectedProgExp.note }}
            </div>

            <div v-if="selectedProgExp">
              <div class="flex items-center justify-between mb-2">
                <div class="text-sm font-bold text-gray-300">
                  {{ selectedProgExp.short }}
                </div>
                <div class="flex items-center gap-3">
                  <div
                    class="flex-1 w-40 bg-gray-800 rounded-full h-1.5 overflow-hidden"
                  >
                    <div
                      class="h-full rounded-full transition-all"
                      :class="
                        expCleared(selectedProgExp)
                          ? 'bg-emerald-500'
                          : 'bg-amber-500'
                      "
                      :style="{
                        width: `${(killedInExp(selectedProgExp) / selectedProgExp.bosses.length) * 100}%`,
                      }"
                    ></div>
                  </div>
                  <span class="text-xs text-gray-500 whitespace-nowrap">
                    {{ killedInExp(selectedProgExp) }}/{{
                      selectedProgExp.bosses.length
                    }}
                  </span>
                  <button
                    class="text-xs text-gray-600 hover:text-emerald-400 transition-colors"
                    @click="markAllInExp(selectedProgExp)"
                  >
                    Mark All
                  </button>
                  <button
                    class="text-xs text-gray-600 hover:text-red-400 transition-colors"
                    @click="unmarkAllInExp(selectedProgExp)"
                  >
                    Clear All
                  </button>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-x-6 gap-y-1">
                <label
                  v-for="boss in selectedProgExp.bosses"
                  :key="boss.key"
                  class="flex items-center gap-2 cursor-pointer py-1 group"
                >
                  <div class="relative shrink-0">
                    <input
                      type="checkbox"
                      class="sr-only"
                      :checked="progKills.has(boss.key)"
                      :disabled="loading.prog"
                      @change="toggleKill(boss.key)"
                    />
                    <div
                      class="w-4 h-4 rounded border flex items-center justify-center transition-all"
                      :class="
                        progKills.has(boss.key)
                          ? 'bg-emerald-600 border-emerald-500'
                          : 'bg-gray-800 border-gray-600 group-hover:border-gray-400'
                      "
                    >
                      <svg
                        v-if="progKills.has(boss.key)"
                        class="w-3 h-3 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        stroke-width="3"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    </div>
                  </div>
                  <span
                    class="text-sm flex-1 truncate"
                    :class="
                      progKills.has(boss.key)
                        ? 'text-gray-400 line-through'
                        : 'text-gray-200'
                    "
                  >
                    {{ boss.name }}
                  </span>
                  <span class="text-xs text-gray-700 truncate max-w-[120px]">{{
                    boss.zone
                  }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, inject, onMounted } from 'vue'
import { useApi, owner } from '../api'
const axios = useApi()

const toast = inject<(msg: string, ok?: boolean) => void>('toast')!

// ── Constants ────────────────────────────────────────────────────────────────

const CLASS_NAMES: Record<number, string> = {
  1: 'Warrior',
  2: 'Cleric',
  3: 'Paladin',
  4: 'Ranger',
  5: 'Shadow Knight',
  6: 'Druid',
  7: 'Monk',
  8: 'Bard',
  9: 'Rogue',
  10: 'Shaman',
  11: 'Necromancer',
  12: 'Wizard',
  13: 'Magician',
  14: 'Enchanter',
  15: 'Beastlord',
  16: 'Berserker',
}

const RACE_NAMES: Record<number, string> = {
  1: 'Human',
  2: 'Barbarian',
  3: 'Erudite',
  4: 'Wood Elf',
  5: 'High Elf',
  6: 'Dark Elf',
  7: 'Half Elf',
  8: 'Dwarf',
  9: 'Troll',
  10: 'Ogre',
  11: 'Halfling',
  12: 'Gnome',
  128: 'Iksar',
  130: 'Vah Shir',
  522: 'Froglok',
  630: 'Drakkin',
}

const EXPANSIONS = [
  { name: 'Classic', max_level: 50 },
  { name: 'Ruins of Kunark', max_level: 60 },
  { name: 'Scars of Velious', max_level: 60 },
  { name: 'Shadows of Luclin', max_level: 65 },
  { name: 'Planes of Power', max_level: 65 },
  { name: 'Legacy of Ykesha', max_level: 65 },
  { name: 'Lost Dungeons of Norrath', max_level: 65 },
  { name: 'Gates of Discord', max_level: 65 },
  { name: 'Omens of War', max_level: 70 },
  { name: 'Dragons of Norrath', max_level: 70 },
  { name: 'Depths of Darkhollow', max_level: 70 },
  { name: 'Prophecy of Ro', max_level: 75 },
  { name: "Serpent's Spine", max_level: 75 },
  { name: 'The Buried Sea', max_level: 75 },
  { name: 'Secrets of Faydwer', max_level: 80 },
  { name: 'Seeds of Destruction', max_level: 85 },
  { name: 'Underfoot', max_level: 85 },
  { name: 'House of Thule', max_level: 90 },
  { name: 'Veil of Alaris', max_level: 95 },
  { name: 'Rain of Fear', max_level: 100 },
]

const STATS = [
  { key: 'str', label: 'STR' },
  { key: 'sta', label: 'STA' },
  { key: 'agi', label: 'AGI' },
  { key: 'dex', label: 'DEX' },
  { key: 'wis', label: 'WIS' },
  { key: 'int', label: 'INT' },
  { key: 'cha', label: 'CHA' },
  { key: 'cur_hp', label: 'HP' },
  { key: 'mana', label: 'Mana' },
]

// ── State ────────────────────────────────────────────────────────────────────

type Character = {
  id: number
  name: string
  level: number
  class: number
  race: number
  zone_id: number
  aa_points: number
  aa_points_spent: number
  exp: number
  str: number
  sta: number
  agi: number
  dex: number
  wis: number
  int: number
  cha: number
  cur_hp: number
  mana: number
  platinum: number
  platinum_bank: number
  gold: number
  silver: number
  copper: number
}

type Zone = {
  id: number
  short_name: string
  long_name: string
  safe_x: number
  safe_y: number
  safe_z: number
}
type ProgBoss = { key: string; name: string; zone: string; zone_short?: string }
type ProgExp = {
  expansion_id: number
  short: string
  bosses: ProgBoss[]
  note?: string
}

const chars = ref<Character[]>([])
const zones = ref<Zone[]>([])
const selected = ref<Character | null>(null)
const search = ref('')
const skillResult = ref('')

// Progression state
const progBosses = ref<ProgExp[]>([])
const progKills = ref<Set<string>>(new Set())
const progExpIdx = ref(0)

const loading = reactive({
  chars: false,
  boost: false,
  currency: false,
  aa: false,
  skills: false,
  teleport: false,
  prog: false,
})

const boost = reactive({ expansionIdx: 18, customLevel: null as number | null })
const currency = reactive({ custom: 0 })
const aa = reactive({ custom: 0 })
const teleport = reactive({
  search: '',
  selectedZone: null as Zone | null,
  x: 0,
  y: 0,
  z: 0,
})

// ── Computed ─────────────────────────────────────────────────────────────────

const filteredChars = computed(() =>
  chars.value.filter((c) =>
    c.name.toLowerCase().includes(search.value.toLowerCase())
  )
)

const filteredZones = computed(() => {
  const q = teleport.search.toLowerCase()
  if (!q) return zones.value.slice(0, 80)
  return zones.value
    .filter(
      (z) =>
        z.long_name.toLowerCase().includes(q) ||
        z.short_name.toLowerCase().includes(q)
    )
    .slice(0, 80)
})

const boostTarget = computed(
  () => boost.customLevel ?? EXPANSIONS[boost.expansionIdx].max_level
)

const selectedProgExp = computed(
  () =>
    progBosses.value.find((e) => e.expansion_id === progExpIdx.value) ?? null
)

const killedInExp = (exp: ProgExp) =>
  exp.bosses.filter((b) => progKills.value.has(b.key)).length

const expCleared = (exp: ProgExp) =>
  exp.bosses.length > 0 && killedInExp(exp) === exp.bosses.length

const expStarted = (exp: ProgExp) => killedInExp(exp) > 0

const totalBosses = computed(() =>
  progBosses.value.reduce((s, e) => s + e.bosses.length, 0)
)
const totalCleared = computed(() =>
  progBosses.value.reduce((s, e) => s + killedInExp(e), 0)
)
const expansionsCleared = computed(
  () => progBosses.value.filter(expCleared).length
)

// ── Loaders ──────────────────────────────────────────────────────────────────

async function loadChars() {
  loading.chars = true
  try {
    const { data } = await axios.get('/api/characters')
    chars.value = data
  } catch (e: any) {
    toast('Failed to load characters: ' + e.message, false)
  } finally {
    loading.chars = false
  }
}

async function loadZones() {
  try {
    const { data } = await axios.get('/api/zones')
    zones.value = data
  } catch {}
}

function selectChar(c: Character) {
  if (owner.busy) return
  owner.subject = c.name
  selected.value = { ...c }
  skillResult.value = ''
  loadProgression(c.id)
}

function onZoneSelect(e: Event) {
  const zone = teleport.selectedZone
  if (zone) {
    teleport.x = zone.safe_x
    teleport.y = zone.safe_y
    teleport.z = zone.safe_z
  }
}

// ── Actions ──────────────────────────────────────────────────────────────────

async function doBoost() {
  if (!selected.value) return
  loading.boost = true
  try {
    const { data } = await axios.post(
      `/api/character/${selected.value.id}/boost`,
      { level: boostTarget.value }
    )
    selected.value.level = data.level
    const c = chars.value.find((x) => x.id === selected.value!.id)
    if (c) c.level = data.level
    if (data.capped) {
      toast(
        `Boosted to Lv ${data.level} — expansion cap is ${data.maxLevel}, requested ${boostTarget.value} was reduced`
      )
    } else {
      toast(`${selected.value.name} boosted to level ${data.level}!`)
    }
  } catch (e: any) {
    toast('Boost failed: ' + (e.response?.data?.error ?? e.message), false)
  } finally {
    loading.boost = false
  }
}

async function grantPlat(amount: number) {
  if (!selected.value || !amount) return
  loading.currency = true
  try {
    await axios.post(`/api/character/${selected.value.id}/currency`, {
      platinum: amount,
    })
    if (selected.value.platinum === undefined) selected.value.platinum = 0
    selected.value.platinum += amount
    toast(
      `Granted ${amount.toLocaleString()} platinum to ${selected.value.name}`
    )
  } catch (e: any) {
    toast(
      'Currency grant failed: ' + (e.response?.data?.error ?? e.message),
      false
    )
  } finally {
    loading.currency = false
  }
}

async function grantAA(points: number) {
  if (!selected.value || !points) return
  loading.aa = true
  try {
    await axios.post(`/api/character/${selected.value.id}/aa`, { points })
    if (selected.value.aa_points === undefined) selected.value.aa_points = 0
    selected.value.aa_points += points
    toast(`Granted ${points.toLocaleString()} AA to ${selected.value.name}`)
  } catch (e: any) {
    toast('AA grant failed: ' + (e.response?.data?.error ?? e.message), false)
  } finally {
    loading.aa = false
  }
}

async function doMaxSkills() {
  if (!selected.value) return
  loading.skills = true
  skillResult.value = ''
  try {
    const { data } = await axios.post(
      `/api/character/${selected.value.id}/maxskills`
    )
    skillResult.value = `${data.updated} skills maxed for ${CLASS_NAMES[selected.value.class]} Lv ${selected.value.level}`
    toast(skillResult.value)
  } catch (e: any) {
    toast('Skill max failed: ' + (e.response?.data?.error ?? e.message), false)
  } finally {
    loading.skills = false
  }
}

async function doTeleport() {
  if (!selected.value || !teleport.selectedZone) return
  loading.teleport = true
  try {
    await axios.post(`/api/character/${selected.value.id}/teleport`, {
      zone_id: teleport.selectedZone.id,
      x: teleport.x,
      y: teleport.y,
      z: teleport.z,
    })
    selected.value.zone_id = teleport.selectedZone.id
    toast(`${selected.value.name} → ${teleport.selectedZone.long_name}`)
  } catch (e: any) {
    toast('Teleport failed: ' + (e.response?.data?.error ?? e.message), false)
  } finally {
    loading.teleport = false
  }
}

async function loadProgression(charId: number) {
  try {
    const { data } = await axios.get(`/api/character/${charId}/progression`)
    if (selected.value?.id === charId) progKills.value = new Set(data.kills)
  } catch (e: any) {
    toast('Progression unavailable: ' + e.message, false)
  }
}

async function toggleKill(bossKey: string) {
  if (!selected.value || loading.prog) return
  loading.prog = true
  const wasKilled = progKills.value.has(bossKey)
  // Optimistic update
  if (wasKilled) progKills.value.delete(bossKey)
  else progKills.value.add(bossKey)
  progKills.value = new Set(progKills.value)
  try {
    if (wasKilled) {
      await axios.delete(
        `/api/character/${selected.value.id}/progression/${bossKey}`
      )
    } else {
      await axios.post(
        `/api/character/${selected.value.id}/progression/${bossKey}`
      )
    }
  } catch (e: any) {
    // Revert on failure
    if (wasKilled) progKills.value.add(bossKey)
    else progKills.value.delete(bossKey)
    progKills.value = new Set(progKills.value)
    toast(
      'Progression update failed: ' + (e.response?.data?.error ?? e.message),
      false
    )
  } finally {
    loading.prog = false
  }
}

async function markAllInExp(exp: ProgExp) {
  await setExpansionKills(exp, true)
}

async function unmarkAllInExp(exp: ProgExp) {
  await setExpansionKills(exp, false)
}

async function setExpansionKills(exp: ProgExp, killed: boolean) {
  const characterId = selected.value?.id
  if (!characterId || loading.prog) return
  loading.prog = true
  try {
    await axios.patch(`/api/character/${characterId}/progression`, {
      keys: exp.bosses.map((b) => b.key),
      killed,
    })
    await loadProgression(characterId)
    toast(`${exp.short} progression saved`)
  } catch (e: any) {
    toast('Progression update failed: ' + e.message, false)
  } finally {
    loading.prog = false
  }
}

// ── Init ─────────────────────────────────────────────────────────────────────

onMounted(async () => {
  loadChars()
  loadZones()
  try {
    const { data } = await axios.get('/api/progression/bosses')
    progBosses.value = data
  } catch {}
})
</script>

<template>
  <div class="p-6 max-w-5xl space-y-5">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">Expansion Lock</h1>
      <p class="text-gray-500 text-sm mt-1">
        Lock the server to a specific EverQuest era. Controls zone access, AA
        availability, and level cap.
      </p>
    </div>

    <!-- Current Status -->
    <div class="card flex items-center justify-between">
      <div v-if="status">
        <div class="text-xs text-gray-500 uppercase tracking-widest mb-1">
          Current Lock
        </div>
        <div class="flex items-center gap-3">
          <span class="text-2xl font-bold text-amber-400">{{
            status.expansion_name
          }}</span>
          <span class="text-gray-500">·</span>
          <span class="text-gray-300">Level Cap {{ status.max_level }}</span>
          <span class="text-gray-500">·</span>
          <span class="text-gray-500 text-sm">{{ status.year }}</span>
        </div>
        <div class="text-xs text-gray-600 mt-1">
          Expansion ID {{ status.expansion_id }}
        </div>
        <div
          v-if="motd"
          class="mt-2 text-xs text-gray-500 italic border-t border-gray-800 pt-2"
        >
          <span class="text-gray-700 not-italic mr-1">MOTD:</span>{{ motd }}
        </div>
      </div>
      <div v-else class="text-gray-500 text-sm">Loading…</div>

      <button @click="loadStatus" class="btn-ghost text-xs">↺ Refresh</button>
    </div>

    <!-- Expansion Selector -->
    <div>
      <div class="card-title">Select Target Expansion</div>
      <div class="overflow-x-auto pb-2">
        <div class="flex gap-2 min-w-max">
          <button
            v-for="exp in expansions"
            :key="exp.id"
            @click="selectExpansion(exp)"
            class="flex-col items-start px-3 py-2.5 rounded border transition-all text-left min-w-[90px]"
            :class="[
              selected?.id === exp.id
                ? 'bg-amber-600/20 border-amber-500 text-white'
                : status?.expansion_id === exp.id
                  ? 'bg-blue-900/20 border-blue-700 text-blue-300'
                  : 'bg-gray-900 border-gray-800 text-gray-400 hover:border-gray-600 hover:text-gray-200',
            ]"
          >
            <div class="font-bold text-xs">{{ exp.short }}</div>
            <div class="text-gray-500 text-xs">{{ exp.year }}</div>
            <div
              class="text-xs mt-0.5 font-mono"
              :class="
                selected?.id === exp.id ? 'text-amber-300' : 'text-gray-600'
              "
            >
              Lv {{ exp.max_level }}
            </div>
            <div
              v-if="status?.expansion_id === exp.id"
              class="text-xs text-blue-400 mt-0.5 font-bold"
            >
              ACTIVE
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Preview Panel -->
    <div v-if="selected" class="space-y-4">
      <div class="flex items-center gap-3 border-b border-gray-800 pb-3">
        <h2 class="text-lg font-bold text-white">
          Preview: {{ selected.name }}
          <span class="text-gray-500 font-normal text-sm"
            >({{ selected.year }})</span
          >
        </h2>
        <div v-if="loadingPreview" class="text-gray-500 text-sm">
          Loading preview…
        </div>
      </div>

      <div v-if="preview" class="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <!-- Level Cap -->
        <div class="card">
          <div class="card-title">Level Cap</div>
          <div class="flex items-center gap-2">
            <span
              class="font-mono text-2xl"
              :class="
                preview.current_max_level !== selected.max_level
                  ? 'text-yellow-400 line-through opacity-50'
                  : 'text-green-400'
              "
            >
              {{ preview.current_max_level }}
            </span>
            <span
              v-if="preview.current_max_level !== selected.max_level"
              class="text-gray-500"
              >→</span
            >
            <span
              v-if="preview.current_max_level !== selected.max_level"
              class="font-mono text-2xl text-green-400"
            >
              {{ selected.max_level }}
            </span>
          </div>
          <div
            v-if="preview.chars_over_cap > 0"
            class="mt-2 text-xs text-yellow-500"
          >
            ⚠ {{ preview.chars_over_cap }} character(s) will be capped to
            {{ selected.max_level }}
          </div>
          <div v-else class="mt-2 text-xs text-gray-600">
            No characters over cap
          </div>
        </div>

        <!-- Zones -->
        <div class="card">
          <div class="card-title">Zone Access</div>
          <div class="space-y-1 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-500">Zones locked</span>
              <span class="font-mono text-red-400">{{
                preview.locked_zone_count
              }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">Added in this era</span>
              <span class="font-mono text-green-400">{{
                preview.added_zone_count
              }}</span>
            </div>
          </div>
          <div class="mt-2 text-xs text-gray-600">
            Via <code class="text-gray-500">Expansion:CurrentExpansion</code>
          </div>
        </div>

        <!-- AAs -->
        <div class="card">
          <div class="card-title">Alternate Abilities</div>
          <div class="space-y-1 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-500">AA ranks hidden</span>
              <span class="font-mono text-red-400">{{
                preview.hidden_aa_count
              }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">AA ranks accessible</span>
              <span class="font-mono text-green-400">{{
                preview.accessible_aa_count
              }}</span>
            </div>
          </div>
          <div class="mt-2 text-xs text-gray-600">
            Via
            <code class="text-gray-500">UseCurrentExpansionAAOnly=true</code>
          </div>
        </div>

        <!-- Client Models -->
        <div class="card">
          <div class="card-title">Client Models</div>
          <div v-if="preview.client.ini_found">
            <div class="flex items-center gap-2">
              <span
                class="font-mono text-sm"
                :class="
                  preview.client.will_change
                    ? 'text-yellow-400 line-through opacity-50'
                    : 'text-green-400'
                "
              >
                {{
                  preview.client.current_all_luclin_off === 'TRUE'
                    ? '2D Classic'
                    : '3D Luclin'
                }}
              </span>
              <span v-if="preview.client.will_change" class="text-gray-500"
                >→</span
              >
              <span
                v-if="preview.client.will_change"
                class="font-mono text-sm text-green-400"
              >
                {{
                  preview.client.target_all_luclin_off === 'TRUE'
                    ? '2D Classic'
                    : '3D Luclin'
                }}
              </span>
            </div>
            <div
              class="mt-2 text-xs"
              :class="
                preview.client.will_change ? 'text-amber-600' : 'text-gray-600'
              "
            >
              {{
                preview.client.will_change
                  ? 'eqclient.ini will be updated'
                  : 'Already correct, no change'
              }}
            </div>
            <div class="mt-1 text-xs text-gray-700">AllLuclinPcModelsOff</div>
          </div>
          <div v-else class="text-xs text-gray-600">
            eqclient.ini not found — skipped
          </div>
        </div>
      </div>

      <!-- Tabs: Zone list / Limitations -->
      <div v-if="preview" class="card">
        <div class="flex gap-4 border-b border-gray-800 mb-4">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            class="pb-2 text-sm font-medium border-b-2 transition-colors -mb-px"
            :class="
              activeTab === tab.key
                ? 'border-amber-500 text-amber-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            "
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Zones Added Tab -->
        <div v-if="activeTab === 'added'">
          <div class="text-xs text-gray-500 mb-2">
            {{ preview.added_zones.length }} zones introduced in
            {{ selected.name }}
          </div>
          <div class="grid grid-cols-2 gap-1 max-h-48 overflow-y-auto">
            <div
              v-for="z in preview.added_zones"
              :key="z.short_name"
              class="text-xs bg-green-900/20 border border-green-800/30 rounded px-2 py-1 text-green-300"
            >
              {{ z.long_name }}
              <span class="text-green-800 ml-1">({{ z.short_name }})</span>
            </div>
          </div>
          <div v-if="!preview.added_zones.length" class="text-gray-600 text-sm">
            No zones added in this specific expansion.
          </div>
        </div>

        <!-- Locked Zones Tab -->
        <div v-if="activeTab === 'locked'">
          <div class="text-xs text-gray-500 mb-2">
            {{ preview.locked_zone_count }} zones from higher expansions
          </div>
          <div
            v-for="group in lockedZonesByExp"
            :key="group.exp_id"
            class="mb-3"
          >
            <div
              class="text-xs font-bold text-gray-400 mb-1 flex items-center gap-2"
            >
              <span class="text-red-500">🔒</span>
              {{ expansionName(group.exp_id) }}
              <span class="text-gray-600 font-normal"
                >({{ group.zones.length }} zones)</span
              >
            </div>
            <div class="grid grid-cols-2 gap-1 ml-4">
              <div
                v-for="z in group.zones.slice(0, 20)"
                :key="z.short_name"
                class="text-xs text-gray-500 truncate"
              >
                {{ z.long_name }}
              </div>
              <div
                v-if="group.zones.length > 20"
                class="text-xs text-gray-700 col-span-2"
              >
                + {{ group.zones.length - 20 }} more…
              </div>
            </div>
          </div>
        </div>

        <!-- Limitations Tab -->
        <div v-if="activeTab === 'limits'" class="space-y-3">
          <div
            class="text-xs text-gray-400 font-bold uppercase tracking-widest mb-3"
          >
            What This Lock DOES Handle
          </div>
          <div
            v-for="item in handled"
            :key="item.label"
            class="flex gap-3 text-sm"
          >
            <span class="text-green-400 shrink-0">✓</span>
            <div>
              <span class="text-gray-200">{{ item.label }}</span>
              <span class="text-gray-600 ml-2 text-xs">{{ item.note }}</span>
            </div>
          </div>

          <div
            class="text-xs text-gray-400 font-bold uppercase tracking-widest mt-4 mb-3"
          >
            What Requires Manual Work
          </div>
          <div
            v-for="item in notHandled"
            :key="item.label"
            class="flex gap-3 text-sm"
          >
            <span class="text-yellow-500 shrink-0">⚠</span>
            <div>
              <span class="text-gray-300">{{ item.label }}</span>
              <div class="text-gray-600 text-xs mt-0.5">{{ item.detail }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Apply Button -->
      <div class="flex items-center gap-4">
        <button
          class="btn-primary px-8 py-3 text-base font-bold"
          :disabled="
            loading || !preview || selected?.id === status?.expansion_id
          "
          @click="showConfirm = true"
        >
          {{
            loading ? 'Applying…' : `LOCK TO ${selected?.name?.toUpperCase()}`
          }}
        </button>
        <div
          v-if="selected?.id === status?.expansion_id"
          class="text-gray-500 text-sm"
        >
          This expansion is already active.
        </div>
        <div v-else class="text-gray-600 text-xs">
          Requires server zone reload to take effect in active zones.
        </div>
      </div>
    </div>

    <!-- Applied Changes Log -->
    <div v-if="appliedChanges.length" class="card border-green-800/40">
      <div class="card-title text-green-500">Applied Changes</div>
      <div class="space-y-1">
        <div
          v-for="(c, i) in appliedChanges"
          :key="i"
          class="flex items-center gap-2 text-sm"
        >
          <span>{{ c.icon }}</span>
          <span :class="c.warning ? 'text-yellow-400' : 'text-gray-300'">{{
            c.label
          }}</span>
        </div>
      </div>
      <div class="mt-3 text-xs text-yellow-600">
        Reload zones or restart the server for all changes to take full effect.
      </div>
    </div>

    <!-- Confirm Dialog -->
    <Teleport to="body">
      <div
        v-if="showConfirm"
        class="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
        @click.self="showConfirm = false"
      >
        <div
          class="bg-gray-900 border border-gray-700 rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl"
        >
          <h3 class="text-lg font-bold text-white mb-2">
            Apply Expansion Lock?
          </h3>
          <p class="text-gray-400 text-sm mb-4">
            This will immediately change
            <strong class="text-amber-400">Expansion:CurrentExpansion</strong>
            to <strong class="text-white">{{ selected?.name }}</strong> ({{
              selected?.year
            }}), set the level cap to
            <strong class="text-white">{{ selected?.max_level }}</strong
            >, and cap any characters above that level.
          </p>
          <div
            v-if="preview?.client?.will_change"
            class="bg-blue-900/20 border border-blue-800/50 rounded p-3 mb-4 text-sm text-blue-300"
          >
            🖥 <strong>eqclient.ini</strong> will be updated:
            <code class="text-blue-200">AllLuclinPcModelsOff</code> →
            <strong>{{ preview.client.target_all_luclin_off }}</strong>
            <span class="text-blue-500 ml-1"
              >({{ preview.client.models_label }})</span
            >
          </div>
          <div
            v-if="preview?.chars_over_cap"
            class="bg-yellow-900/30 border border-yellow-800/50 rounded p-3 mb-4 text-sm text-yellow-300"
          >
            ⚠ {{ preview.chars_over_cap }} character(s) will have their level
            reduced to {{ selected?.max_level }}.
          </div>
          <div class="flex gap-3 justify-end">
            <button class="btn-ghost" @click="showConfirm = false">
              Cancel
            </button>
            <button class="btn-primary px-6" @click="applyLock">
              Apply Lock
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject, onMounted, watch } from 'vue'
import axios from 'axios'

const toast = inject<(msg: string, ok?: boolean) => void>('toast')!

type ExpansionDef = {
  id: number
  name: string
  short: string
  max_level: number
  year: number
}
type ExpansionStatus = {
  expansion_id: number
  expansion_name: string
  expansion_short: string
  max_level: number
  year: number
}
type Preview = {
  target: ExpansionDef
  current_expansion_id: number
  current_max_level: number
  locked_zone_count: number
  added_zone_count: number
  locked_zones: { long_name: string; short_name: string; expansion: number }[]
  added_zones: { long_name: string; short_name: string }[]
  zones_by_exp: { expansion: number; count: number }[]
  hidden_aa_count: number
  accessible_aa_count: number
  chars_over_cap: number
  client: {
    current_all_luclin_off: string | null
    target_all_luclin_off: string
    models_label: string
    will_change: boolean
    ini_found: boolean
  }
}

const expansions = ref<ExpansionDef[]>([])
const status = ref<ExpansionStatus | null>(null)
const motd = ref<string>('')
const selected = ref<ExpansionDef | null>(null)
const preview = ref<Preview | null>(null)
const loadingPreview = ref(false)
const loading = ref(false)
const showConfirm = ref(false)
const activeTab = ref('added')
const appliedChanges = ref<
  { icon: string; label: string; warning?: boolean }[]
>([])

const tabs = [
  { key: 'added', label: 'Zones Added' },
  { key: 'locked', label: 'Zones Locked' },
  { key: 'limits', label: 'Scope & Limitations' },
]

const handled = [
  {
    label: 'Zone access',
    note: 'Via Expansion:CurrentExpansion + zone.expansion field',
  },
  {
    label: 'Level cap',
    note: 'Character:MaxLevel and Character:MaxExpLevel rules',
  },
  {
    label: 'AA visibility',
    note: 'Via UseCurrentExpansionAAOnly=true + aa_ranks.expansion',
  },
  {
    label: 'Spell gating',
    note: 'Naturally enforced by level cap — higher-level spells require higher levels',
  },
  {
    label: 'Character level cap enforcement',
    note: 'Characters over the new cap are immediately reduced',
  },
]
const notHandled = [
  {
    label: 'Quest scripts',
    detail:
      'Perl/Lua quests run regardless of expansion. Authentic quest content requires separate quest folder sets per era, or per-quest expansion checks. This is a major project if needed.',
  },
  {
    label: 'Existing character items',
    detail:
      "Players already carrying gear from higher expansions keep those items. A full item audit would need to check each character's inventory against era-appropriate items.",
  },
  {
    label: 'Low-level expansion spells',
    detail:
      "Some expansions added spells available at level 20-50. These won't be blocked by the level cap alone. Requires per-spell expansion tagging to enforce.",
  },
  {
    label: 'Expansion-specific NPC spawns in classic zones',
    detail:
      'Some NPCs added post-Classic appear in old zones. Requires per-NPC spawn condition management.',
  },
]

const lockedZonesByExp = computed(() => {
  if (!preview.value) return []
  const groups: Record<
    number,
    { exp_id: number; zones: typeof preview.value.locked_zones }
  > = {}
  for (const z of preview.value.locked_zones) {
    if (!groups[z.expansion])
      groups[z.expansion] = { exp_id: z.expansion, zones: [] }
    groups[z.expansion].zones.push(z)
  }
  return Object.values(groups).sort((a, b) => a.exp_id - b.exp_id)
})

function expansionName(id: number): string {
  return expansions.value.find((e) => e.id === id)?.name ?? `Expansion ${id}`
}

async function loadStatus() {
  try {
    const [s, e, m] = await Promise.all([
      axios.get('/api/expansion/status'),
      axios.get('/api/expansions'),
      axios.get('/api/motd'),
    ])
    status.value = s.data
    expansions.value = e.data
    motd.value = m.data.motd ?? ''
    // Pre-select the currently active expansion
    if (!selected.value) {
      selected.value =
        expansions.value.find((e) => e.id === s.data.expansion_id) ?? null
      if (selected.value) await loadPreview()
    }
  } catch (e: any) {
    toast('Failed to load expansion status: ' + e.message, false)
  }
}

async function selectExpansion(exp: ExpansionDef) {
  selected.value = exp
  activeTab.value = 'added'
  await loadPreview()
}

async function loadPreview() {
  if (!selected.value) return
  loadingPreview.value = true
  preview.value = null
  try {
    const { data } = await axios.get(
      `/api/expansion/${selected.value.id}/preview`
    )
    preview.value = data
  } catch (e: any) {
    toast('Preview failed: ' + e.message, false)
  } finally {
    loadingPreview.value = false
  }
}

async function applyLock() {
  if (!selected.value) return
  showConfirm.value = false
  loading.value = true
  try {
    const { data } = await axios.post('/api/expansion/apply', {
      expansion_id: selected.value.id,
    })
    appliedChanges.value = data.changes
    status.value = {
      expansion_id: selected.value.id,
      expansion_name: selected.value.name,
      expansion_short: selected.value.short,
      max_level: selected.value.max_level,
      year: selected.value.year,
    }
    motd.value = `[LocalDev] Era: ${selected.value.name} (${selected.value.short}) — Level Cap ${selected.value.max_level} — ${selected.value.year}`
    toast(
      `Locked to ${selected.value.name} (Level ${selected.value.max_level})`
    )
    await loadPreview()
  } catch (e: any) {
    toast('Apply failed: ' + (e.response?.data?.error ?? e.message), false)
  } finally {
    loading.value = false
  }
}

onMounted(loadStatus)
</script>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from '../api'
const api = useApi()
type Expansion = { id: number; name: string; max_level: number }
const expansions = ref<Expansion[]>([])
const status = ref<any>(null)
const preview = ref<any>(null)
const selected = ref(0)
const error = ref('')
const loading = ref(false)
async function loadPreview() {
  const target = selected.value
  loading.value = true
  error.value = ''
  try {
    const result = await api.get(`/api/expansion/${target}/preview`)
    if (selected.value === target) preview.value = result.data
  } catch (e: any) {
    error.value = e.message
  } finally {
    if (selected.value === target) loading.value = false
  }
}
async function load() {
  try {
    const [current, choices] = await Promise.all([
      api.get('/api/expansion/status'),
      api.get('/api/expansions'),
    ])
    status.value = current.data
    expansions.value = choices.data
    selected.value = current.data.expansion_id
    await loadPreview()
  } catch (e: any) {
    error.value = e.message
  }
}
function downloadProposal() {
  if (!preview.value) return
  const target = preview.value.target
  const proposal = {
    expansion: target.id,
    name: target.name,
    max_level: target.max_level,
    aa_open: status.value.declared.aa_open,
    luclin_models: target.id >= 3,
  }
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(proposal, null, 2) + String.fromCharCode(10)], {
      type: 'application/json',
    })
  )
  const link = document.createElement('a')
  link.href = url
  link.download = 'era-proposal.json'
  link.click()
  URL.revokeObjectURL(url)
}
onMounted(load)
</script>
<template>
  <section class="p-6 max-w-5xl space-y-5">
    <div>
      <h1 class="text-2xl font-bold">Expansion lock</h1>
      <p class="text-sm text-gray-400 mt-1">
        Inspect the current era and prepare the next release.
      </p>
    </div>
    <p v-if="error" role="alert" class="text-red-300">{{ error }}</p>
    <div v-if="status" class="card">
      <h2 class="font-semibold">
        Current: {{ status.expansion_name }} · Level {{ status.max_level }}
      </h2>
      <p class="text-sm text-gray-400 mt-2">
        Committed configuration: {{ status.declared.name }} · Level
        {{ status.declared.max_level }}. AA era filtering is
        {{ status.aa_open ? 'off' : 'on' }}.
      </p>
    </div>
    <label class="block text-sm" for="target-era">Preview an expansion</label
    ><select
      id="target-era"
      v-model="selected"
      class="select max-w-full"
      @change="loadPreview"
    >
      <option v-for="exp in expansions" :key="exp.id" :value="exp.id">
        {{ exp.name }} · Level {{ exp.max_level }}
      </option>
    </select>
    <p v-if="loading" role="status">Loading preview…</p>
    <template v-else-if="preview">
      <div class="grid sm:grid-cols-3 gap-3">
        <div class="card">
          <p class="text-gray-400 text-sm">Zones outside era</p>
          <p class="text-2xl mt-1">{{ preview.locked_zone_count }}</p>
        </div>
        <div class="card">
          <p class="text-gray-400 text-sm">Zones in expansion</p>
          <p class="text-2xl mt-1">{{ preview.added_zone_count }}</p>
        </div>
        <div class="card">
          <p class="text-gray-400 text-sm">Characters above cap</p>
          <p class="text-2xl mt-1">{{ preview.chars_over_cap }}</p>
        </div>
      </div>
      <div class="card space-y-3">
        <h2 class="font-semibold">
          Era activation requires a reviewed release
        </h2>
        <p class="text-sm text-gray-300">
          Repository policy requires committing era.json, reviewing the spell
          merchant catalog, and using the apply-era release process. Download
          this proposal for that review. No character levels or client files
          change here.
        </p>
        <button class="btn-primary" @click="downloadProposal">
          Download era proposal
        </button>
      </div>
      <details class="card">
        <summary class="cursor-pointer font-semibold">
          Zones in {{ preview.target.name }}
        </summary>
        <ul class="mt-3 grid sm:grid-cols-2 gap-1 text-sm text-gray-300">
          <li v-for="zone in preview.added_zones" :key="zone.short_name">
            {{ zone.long_name }}
          </li>
        </ul>
      </details>
      <details class="card">
        <summary class="cursor-pointer font-semibold">
          Zones outside the proposed era (first 300)
        </summary>
        <ul class="mt-3 grid sm:grid-cols-2 gap-1 text-sm text-gray-300">
          <li
            v-for="zone in preview.locked_zones"
            :key="`${zone.short_name}:${zone.expansion}`"
          >
            {{ zone.long_name }}
          </li>
        </ul>
      </details>
      <p class="text-sm text-gray-400">
        Preview does not audit existing gear, quest scripts or
        expansion-specific NPCs. Level limits alone do not enforce spell
        availability. Character capping requires a separate explicit release
        action.
      </p>
    </template>
  </section>
</template>

<template>
  <div class="p-6 max-w-3xl">
    <h1 class="text-2xl font-bold text-white mb-1">Server Tweaks</h1>
    <p class="text-gray-500 text-sm mb-6">Adjust live server rules. Changes take effect on next zone/server reload.</p>

    <div v-if="loading" class="text-gray-500 text-sm">Loading rules…</div>

    <div v-else class="space-y-4">

      <!-- XP Rate -->
      <div class="card">
        <div class="card-title">Experience Rate</div>
        <RuleRow
          v-for="r in ruleGroup('Character')"
          :key="r.rule_name"
          :rule="r"
          @save="saveRule"
        />
      </div>

      <!-- Loot -->
      <div class="card">
        <div class="card-title">Loot Multipliers</div>
        <RuleRow
          v-for="r in ruleGroup('Zone')"
          :key="r.rule_name"
          :rule="r"
          @save="saveRule"
        />
      </div>

      <!-- AA -->
      <div class="card">
        <div class="card-title">AA Experience</div>
        <RuleRow
          v-for="r in ruleGroup('AA')"
          :key="r.rule_name"
          :rule="r"
          @save="saveRule"
        />
      </div>

    </div>

    <div class="mt-6 card bg-yellow-900/20 border-yellow-800/50">
      <div class="card-title text-yellow-600">Quick Presets</div>
      <div class="flex gap-3 flex-wrap">
        <button class="btn-green" @click="applyPreset('casual')">Casual Solo</button>
        <button class="btn-primary" @click="applyPreset('boosted')">Boosted (5x XP)</button>
        <button class="btn-ghost" @click="applyPreset('default')">Reset Defaults</button>
      </div>
      <div class="mt-2 text-xs text-gray-600">
        Casual: 3x XP, 2x Loot · Boosted: 5x XP, 3x Loot · Default: server stock values
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject, onMounted, defineComponent, h } from 'vue'
import axios from 'axios'

const toast = inject<(msg: string, ok?: boolean) => void>('toast')!

type Rule = { ruleset_id: number; rule_name: string; rule_value: string; notes: string }

const rules = ref<Rule[]>([])
const loading = ref(true)

const ruleGroup = (prefix: string) =>
  rules.value.filter(r => r.rule_name.startsWith(prefix + ':'))

async function loadRules() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/rules')
    rules.value = data
  } catch (e: any) {
    toast('Failed to load rules: ' + e.message, false)
  } finally {
    loading.value = false
  }
}

async function saveRule(ruleName: string, value: string) {
  try {
    await axios.patch(`/api/rules/${encodeURIComponent(ruleName)}`, { value })
    const r = rules.value.find(x => x.rule_name === ruleName)
    if (r) r.rule_value = value
    toast(`${ruleName} → ${value}`)
  } catch (e: any) {
    toast('Save failed: ' + (e.response?.data?.error ?? e.message), false)
  }
}

const PRESETS: Record<string, Record<string, string>> = {
  casual: {
    'Character:ExpMultiplier': '3',
    'Zone:GlobalLootMultiplier': '2',
    'AA:ExpPerPoint': '7992167',
  },
  boosted: {
    'Character:ExpMultiplier': '5',
    'Zone:GlobalLootMultiplier': '3',
    'AA:ExpPerPoint': '4000000',
  },
  default: {
    'Character:ExpMultiplier': '0.65',
    'Zone:GlobalLootMultiplier': '1',
    'AA:ExpPerPoint': '23976503',
  },
}

async function applyPreset(key: string) {
  const preset = PRESETS[key]
  for (const [name, val] of Object.entries(preset)) {
    await saveRule(name, val)
  }
  toast(`Applied "${key}" preset`)
}

// ── Inline sub-component for rule rows ───────────────────────────────────────

const RuleRow = defineComponent({
  props: { rule: Object as () => Rule },
  emits: ['save'],
  setup(props, { emit }) {
    const editing = ref(props.rule!.rule_value)
    const dirty = computed(() => editing.value !== props.rule!.rule_value)
    return () => h('div', { class: 'flex items-center gap-3 py-2 border-b border-gray-800 last:border-0' }, [
      h('div', { class: 'flex-1 min-w-0' }, [
        h('div', { class: 'text-sm text-gray-200 font-mono' }, props.rule!.rule_name.split(':')[1]),
        h('div', { class: 'text-xs text-gray-600 truncate' }, props.rule!.notes),
      ]),
      h('input', {
        value: editing.value,
        onInput: (e: Event) => { editing.value = (e.target as HTMLInputElement).value },
        class: 'input w-36 font-mono text-right',
        type: 'text',
      }),
      h('button', {
        onClick: () => emit('save', props.rule!.rule_name, editing.value),
        disabled: !dirty.value,
        class: 'btn ' + (dirty.value ? 'btn-primary' : 'btn-ghost opacity-30'),
      }, 'Save'),
    ])
  },
})

onMounted(loadRules)
</script>

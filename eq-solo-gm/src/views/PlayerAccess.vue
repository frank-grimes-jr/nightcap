<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi, owner } from '../api'
const api = useApi()
type Credential = { id: string; player: string; created: string }
const credentials = ref<Credential[]>([])
const ready = ref(false)
const loading = ref(true)
const player = ref('')
const code = ref('')
const message = ref('')
const failed = ref(false)
async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/api/access')
    ready.value = data.ready
    credentials.value = data.credentials
  } catch (error: any) {
    message.value = error.message
    failed.value = true
  } finally {
    loading.value = false
  }
}
async function initialize() {
  try {
    await api.post('/api/access/initialize')
    await load()
    message.value =
      'Registry initialized. Gateway deployment must also be active.'
    failed.value = false
  } catch (error: any) {
    message.value = error.message
    failed.value = true
  }
}
async function issue() {
  code.value = ''
  try {
    const { data } = await api.post('/api/access', { player: player.value })
    code.value = data.code
    message.value = `Code created for ${data.player}.`
    failed.value = false
    await load()
  } catch (error: any) {
    message.value = error.message
    failed.value = true
  }
}
async function revoke(credential: Credential) {
  owner.subject = credential.player
  try {
    await api.delete(`/api/access/${credential.id}`)
    message.value = `Access revoked for ${credential.player}.`
    failed.value = false
    code.value = ''
    await load()
  } catch (error: any) {
    message.value = error.message
    failed.value = true
  } finally {
    owner.subject = ''
  }
}
async function copy() {
  try {
    await navigator.clipboard.writeText(code.value)
    message.value = 'Copied. Send this code to the player privately.'
  } catch {
    message.value = 'Select the code and copy it manually.'
  }
}
onMounted(load)
</script>
<template>
  <section class="p-6 max-w-4xl space-y-5">
    <div>
      <h1 class="text-2xl font-bold">Player access</h1>
      <p class="text-gray-400 text-sm mt-1">
        Give a player launcher access that survives IP changes.
      </p>
    </div>
    <p class="text-sm text-gray-300">
      Generate a code here → send it privately → the player pastes it into
      <strong>Player access</strong> in the launcher → Save → Play. Their game
      username and password stay separate.
    </p>
    <p
      v-if="message"
      role="status"
      :class="failed ? 'text-red-300' : 'text-emerald-300'"
    >
      {{ message }}
    </p>
    <p v-if="loading" role="status">Loading access registry…</p>
    <div v-else-if="!ready" class="card space-y-3">
      <h2 class="font-semibold">Access registry is not ready</h2>
      <p class="text-sm text-gray-400">
        The reviewed player-access gateway must be deployed before these codes
        can admit players.
      </p>
      <button
        v-if="owner.environment === 'production'"
        class="btn-primary"
        @click="initialize"
      >
        Initialize registry
      </button>
      <p v-else class="text-sm">
        Select OVH production to manage player access.
      </p>
    </div>
    <form v-else class="card space-y-3" @submit.prevent="issue">
      <h2 class="font-semibold">Generate an access code</h2>
      <label class="block text-sm" for="player-name">Player name</label
      ><input
        id="player-name"
        class="input max-w-sm"
        v-model="player"
        maxlength="80"
        required
        placeholder="Joe"
      /><button class="btn-primary" :disabled="owner.busy || !player.trim()">
        Generate code
      </button>
    </form>
    <div v-if="code" class="card space-y-3 border-amber-700">
      <h2 class="font-semibold text-amber-300">Copy this code now</h2>
      <p class="text-sm text-gray-300">
        The full code is only shown here. It is not emailed automatically.
      </p>
      <label for="access-code" class="sr-only">Generated access code</label
      ><textarea
        id="access-code"
        class="input font-mono resize-none"
        rows="3"
        readonly
        :value="code"
      />
      <div class="flex gap-2">
        <button class="btn-primary" @click="copy">Copy code</button
        ><button class="btn-ghost" @click="code = ''">Hide code</button>
      </div>
    </div>
    <div v-if="ready">
      <h2 class="font-semibold mb-3">Active codes</h2>
      <p v-if="!credentials.length" class="text-gray-400">
        No active codes yet.
      </p>
      <article
        v-for="credential in credentials"
        :key="credential.id"
        class="py-3 border-b border-gray-800 flex flex-wrap justify-between gap-3"
      >
        <div>
          <p class="font-semibold">{{ credential.player }}</p>
          <p class="text-xs text-gray-400">
            Created {{ new Date(credential.created).toLocaleString() }} ·
            {{ credential.id.slice(0, 8) }}
          </p>
        </div>
        <button class="btn-red" @click="revoke(credential)">Revoke code</button>
      </article>
    </div>
  </section>
</template>

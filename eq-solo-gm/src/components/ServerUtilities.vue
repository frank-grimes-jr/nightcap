<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from '../api'
const api = useApi()
const motd = ref('')
const client = ref<any>(null)
const clientError = ref('')
const message = ref('')
const failed = ref(false)
const history = ref<any[]>([])
const historyError = ref('')
async function loadHistory() {
  try {
    history.value = (await api.get('/api/receipts')).data
    historyError.value = ''
  } catch (error: any) {
    historyError.value = error.message
  }
}
async function saveMotd() {
  try {
    await api.patch('/api/motd', { motd: motd.value })
    message.value = 'Message saved. Resume the game to load it.'
    failed.value = false
    await loadHistory()
  } catch (error: any) {
    message.value = error.message
    failed.value = true
  }
}
async function restock() {
  try {
    const { data } = await api.post('/api/vendors/refresh')
    message.value = data.message
    failed.value = false
  } catch (error: any) {
    message.value = error.message
    failed.value = true
  }
}
async function saveModels() {
  try {
    await api.patch('/api/client/settings', {
      AllLuclinPcModelsOff: client.value.AllLuclinPcModelsOff,
    })
    message.value =
      'Model preference saved on this computer. Restart the game client to load it.'
    failed.value = false
  } catch (error: any) {
    message.value = error.message
    failed.value = true
  }
}
onMounted(async () => {
  await Promise.all([
    api
      .get('/api/motd')
      .then((r) => {
        motd.value = r.data.motd
      })
      .catch((e: any) => {
        message.value = e.message
        failed.value = true
      }),
    api
      .get('/api/client/settings')
      .then((r) => {
        client.value = r.data
      })
      .catch((e: any) => {
        clientError.value = e.message
      }),
    loadHistory(),
  ])
})
</script>
<template>
  <div class="space-y-5 mt-6">
    <p
      v-if="message"
      role="status"
      :class="failed ? 'text-red-300' : 'text-emerald-300'"
    >
      {{ message }}
    </p>
    <form class="card space-y-3" @submit.prevent="saveMotd">
      <h2 class="font-semibold">Message of the day</h2>
      <label class="sr-only" for="motd">Message of the day</label
      ><input id="motd" class="input" v-model="motd" maxlength="500" /><button
        class="btn-primary"
      >
        Save message
      </button>
    </form>
    <div class="card space-y-3">
      <h2 class="font-semibold">Spell merchants</h2>
      <p class="text-sm text-gray-400">
        Restore the reviewed, era-aware catalog during maintenance. Merchant
        identity or catalog drift stops the operation.
      </p>
      <button class="btn-primary" @click="restock">
        Restore canonical stock
      </button>
    </div>
    <form class="card space-y-3" @submit.prevent="saveModels">
      <h2 class="font-semibold">Client models · this computer</h2>
      <p class="text-sm text-gray-400">
        This changes only your configured client copy, even when Production is
        selected.
      </p>
      <p v-if="clientError" class="text-amber-300 text-sm">{{ clientError }}</p>
      <template v-if="client"
        ><p class="text-xs text-gray-400 break-all">{{ client.path }}</p>
        <label for="client-models" class="block text-sm">Character models</label
        ><select
          id="client-models"
          v-model="client.AllLuclinPcModelsOff"
          class="select"
        >
          <option value="TRUE">Classic models</option>
          <option value="FALSE">Luclin models</option></select
        ><button class="btn-primary ml-3">
          Save model preference
        </button></template
      >
    </form>
    <section class="card space-y-3">
      <div class="flex justify-between items-center gap-2">
        <h2 class="font-semibold">Recent database actions</h2>
        <button class="btn-ghost" @click="loadHistory">Refresh history</button>
      </div>
      <p v-if="historyError" class="text-amber-300 text-sm">
        {{ historyError }}
      </p>
      <p v-else-if="!history.length" class="text-gray-400 text-sm">
        No recorded actions.
      </p>
      <ol class="space-y-3">
        <li
          v-for="entry in history"
          :key="entry.request_id"
          class="border-t border-gray-800 pt-3"
        >
          <p class="text-sm break-all">{{ entry.operation }}</p>
          <p class="text-xs text-gray-400">
            {{ new Date(entry.created_at).toLocaleString() }}
          </p>
          <p class="text-xs text-gray-400 break-all">
            Receipt {{ entry.request_id }}
          </p>
        </li>
      </ol>
    </section>
  </div>
</template>

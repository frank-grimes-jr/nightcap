<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi, owner, labels, resolvePendingAction } from '../api'
const api = useApi()
const status = ref<any>(null)
const message = ref('')
const loading = ref(false)
const receipt = ref('')
async function refresh() {
  loading.value = true
  try {
    status.value = (await api.get('/api/status')).data
    message.value = ''
  } catch (error: any) {
    status.value = null
    message.value = error.message
  } finally {
    loading.value = false
  }
}
async function action(url: string) {
  try {
    await api.post(url)
    await refresh()
  } catch (error: any) {
    message.value = error.message
  }
}
async function inspectReceipt() {
  try {
    const { data } = await api.get(`/api/receipts/${owner.uncertain}`)
    receipt.value = data.found
      ? 'This database action committed successfully.'
      : 'No database receipt found. Refresh affected data before retrying. Runtime and access-code actions do not use database receipts.'
  } catch (error: any) {
    receipt.value = error.message
  }
}
async function resolvePending() {
  try {
    await resolvePendingAction()
    receipt.value = ''
    await refresh()
  } catch (error: any) {
    receipt.value = error.message
  }
}
onMounted(refresh)
</script>
<template>
  <div class="px-5 py-3 border-b border-gray-800 bg-gray-900 space-y-2 text-sm">
    <div class="flex flex-wrap items-center gap-3">
      <strong>{{ labels[owner.environment] }}</strong
      ><span v-if="loading" role="status">Connecting…</span
      ><span v-else-if="status">{{
        status.maintenance
          ? 'Maintenance — players disconnected'
          : status.game_running
            ? 'Game running'
            : 'Game stopped'
      }}</span
      ><span v-else class="text-red-300">Connection unavailable</span
      ><button
        class="btn-ghost ml-auto"
        @click="refresh"
        :disabled="loading || owner.busy"
      >
        Refresh status
      </button>
    </div>
    <p v-if="message" role="alert" class="text-red-300">{{ message }}</p>
    <div v-if="status" class="flex flex-wrap gap-2 items-center">
      <button
        v-if="!status.setup_ready"
        class="btn-primary"
        @click="action('/api/setup')"
        :disabled="owner.busy"
      >
        Set up GM controls</button
      ><button
        :class="status.maintenance_active ? 'btn-green' : 'btn-ghost'"
        :disabled="owner.busy"
        @click="
          action(
            status.maintenance_active
              ? '/api/maintenance/end'
              : '/api/maintenance/start'
          )
        "
      >
        {{
          status.maintenance_active ? 'Resume game' : 'Start maintenance'
        }}</button
      ><button
        v-if="status.maintenance_active && !status.maintenance"
        class="btn-ghost"
        @click="action('/api/maintenance/start')"
      >
        Complete shutdown</button
      ><span class="text-xs text-gray-400"
        >Maintenance is required for character, rule, vendor and
        account-deletion changes.</span
      >
    </div>
    <p v-if="status && !status.writes_enabled" class="text-amber-300 text-xs">
      Production preview: changes are disabled pending release approval.
    </p>
    <p
      v-if="
        status &&
        owner.environment === 'production' &&
        !status.credential_gateway_active
      "
      class="text-amber-300 text-xs"
    >
      The IP-independent player gateway has not been activated yet.
    </p>
    <p v-if="owner.busy" role="status" class="text-amber-300">
      Applying action. Keep this window open…
    </p>
    <div
      v-if="owner.uncertain"
      role="alert"
      class="border border-amber-700 p-3 space-y-2"
    >
      <p>
        The last action could not be confirmed. Check its result before
        repeating it.
      </p>
      <p class="font-mono text-xs">{{ owner.uncertain }}</p>
      <button class="btn-ghost" @click="inspectReceipt">
        Check action receipt
      </button>
      <p v-if="receipt">{{ receipt }}</p>
      <button v-if="receipt" class="btn-ghost" @click="resolvePending">
        I checked the result — unlock controls
      </button>
    </div>
  </div>
</template>

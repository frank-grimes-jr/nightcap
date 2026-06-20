<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Account {
  id: number
  account_name: string
  source_loginserver: string
  last_login_date: string | null
  created_at: string | null
}

const accounts = ref<Account[]>([])
const loading = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('')
const selectedId = ref<number | null>(null)
const newPassword = ref('')
const showPasswordForm = ref(false)

const sortedAccounts = computed(() => {
  return [...accounts.value].sort((a, b) => {
    const dateA = a.last_login_date ? new Date(a.last_login_date).getTime() : 0
    const dateB = b.last_login_date ? new Date(b.last_login_date).getTime() : 0
    return dateB - dateA
  })
})

const loadAccounts = async () => {
  loading.value = true
  message.value = ''
  try {
    const res = await fetch('/api/accounts')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    accounts.value = await res.json()
  } catch (err) {
    message.value = `Failed to load accounts: ${err}`
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

const deleteAccount = async (id: number, name: string) => {
  if (!confirm(`Delete account "${name}"? This cannot be undone.`)) return
  try {
    const res = await fetch(`/api/accounts/${id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const result = await res.json()
    message.value = `Deleted account: ${result.deleted}`
    messageType.value = 'success'
    await loadAccounts()
  } catch (err) {
    message.value = `Failed to delete: ${err}`
    messageType.value = 'error'
  }
}

const changePassword = async () => {
  if (!selectedId.value || !newPassword.value) {
    message.value = 'Password required'
    messageType.value = 'error'
    return
  }

  try {
    const res = await fetch(`/api/accounts/${selectedId.value}/password`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_password: newPassword.value }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const result = await res.json()
    message.value = `Password updated for account ${selectedId.value}. Account will be updated to SCrypt on next login.`
    messageType.value = 'success'
    newPassword.value = ''
    showPasswordForm.value = false
    selectedId.value = null
  } catch (err) {
    message.value = `Failed to update password: ${err}`
    messageType.value = 'error'
  }
}

const showForm = (id: number) => {
  selectedId.value = id
  newPassword.value = ''
  showPasswordForm.value = true
}

const cancelForm = () => {
  showPasswordForm.value = false
  selectedId.value = null
  newPassword.value = ''
}

onMounted(() => loadAccounts())
</script>

<template>
  <div class="p-6 bg-gray-900 text-gray-100 min-h-screen">
    <div class="max-w-6xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-3xl font-bold flex items-center gap-2">
          🔐 Account Management
        </h1>
        <button
          @click="loadAccounts"
          :disabled="loading"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded font-semibold"
        >
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>

      <div v-if="message" :class="[
        'p-4 rounded mb-4 font-semibold',
        messageType === 'success' ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'
      ]">
        {{ message }}
      </div>

      <div v-if="showPasswordForm && selectedId" class="bg-gray-800 p-6 rounded mb-6 border border-gray-700">
        <h3 class="text-xl font-bold mb-4">Change Password</h3>
        <p class="text-gray-400 mb-4">Account ID: {{ selectedId }}</p>
        <input
          v-model="newPassword"
          type="password"
          placeholder="New password"
          @keyup.enter="changePassword"
          class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded mb-4 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
        />
        <div class="flex gap-2">
          <button
            @click="changePassword"
            class="px-4 py-2 bg-green-600 hover:bg-green-700 rounded font-semibold"
          >
            Save Password
          </button>
          <button
            @click="cancelForm"
            class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded font-semibold"
          >
            Cancel
          </button>
        </div>
      </div>

      <div v-if="accounts.length === 0" class="text-center text-gray-400 py-12">
        <p v-if="!loading" class="text-lg">No accounts found</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="acc in sortedAccounts"
          :key="acc.id"
          class="bg-gray-800 p-4 rounded border border-gray-700 hover:border-gray-500 transition flex items-center justify-between"
        >
          <div class="flex-1">
            <div class="font-bold text-lg">{{ acc.account_name }}</div>
            <div class="text-sm text-gray-400">
              ID: {{ acc.id }} | Server: {{ acc.source_loginserver }}
            </div>
            <div class="text-xs text-gray-500 mt-1">
              <div v-if="acc.last_login_date">
                Last login: {{ new Date(acc.last_login_date).toLocaleString() }}
              </div>
              <div v-if="acc.created_at">
                Created: {{ new Date(acc.created_at).toLocaleString() }}
              </div>
            </div>
          </div>
          <div class="flex gap-2">
            <button
              @click="showForm(acc.id)"
              class="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm font-semibold"
            >
              Change Password
            </button>
            <button
              @click="deleteAccount(acc.id, acc.account_name)"
              class="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm font-semibold"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

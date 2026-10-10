<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useApi, owner, labels } from '../api'
const api = useApi()
type Account = {
  id: number
  account_name: string
  source_loginserver: string
  last_login_date: string | null
}
const accounts = ref<Account[]>([])
const selected = ref<Account | null>(null)
const password = ref('')
const search = ref('')
const loading = ref(true)
const message = ref('')
const failed = ref(false)
const visible = computed(() =>
  accounts.value.filter((a) =>
    a.account_name.toLowerCase().includes(search.value.toLowerCase())
  )
)
async function load() {
  loading.value = true
  try {
    accounts.value = (await api.get('/api/accounts')).data
  } catch (error: any) {
    message.value = error.message
    failed.value = true
  } finally {
    loading.value = false
  }
}
async function reset() {
  const account = selected.value
  if (!account) return
  try {
    await api.patch(`/api/accounts/${account.id}/password`, {
      account_name: account.account_name,
      source_loginserver: account.source_loginserver,
      new_password: password.value,
    })
    message.value = `Password reset and verified for ${account.account_name}. Share the new password privately.`
    failed.value = false
    selected.value = null
  } catch (error: any) {
    message.value = error.message
    failed.value = true
  } finally {
    password.value = ''
  }
}
async function remove(account: Account) {
  try {
    await api.delete(`/api/accounts/${account.id}`, {
      data: {
        account_name: account.account_name,
        source_loginserver: account.source_loginserver,
      },
    })
    message.value = `${account.account_name} deleted.`
    failed.value = false
    await load()
  } catch (error: any) {
    message.value = error.message
    failed.value = true
  }
}
function cancelPassword() {
  selected.value = null
  password.value = ''
}
function selectAccount(account: Account) {
  selected.value = account
  password.value = ''
}
onMounted(load)
</script>
<template>
  <section class="p-6 max-w-5xl space-y-5">
    <div class="flex justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold">Accounts</h1>
        <p class="text-gray-400 text-sm mt-1">
          Game login credentials Â· {{ labels[owner.environment] }}
        </p>
      </div>
      <button class="btn-ghost" @click="load" :disabled="loading">
        Refresh
      </button>
    </div>
    <p class="text-sm text-gray-400">
      Password resets work while the game is online. Launcher access codes are
      managed under Player access.
    </p>
    <p
      v-if="message"
      role="status"
      :class="failed ? 'text-red-300' : 'text-emerald-300'"
    >
      {{ message }}
    </p>
    <form v-if="selected" class="card space-y-3" @submit.prevent="reset">
      <h2 class="font-bold">Reset password for {{ selected.account_name }}</h2>
      <p class="text-sm text-gray-400">
        Account {{ selected.id }} Â· {{ selected.source_loginserver }} Â·
        {{ labels[owner.environment] }}
      </p>
      <label class="block" for="new-password">New game password</label>
      <input
        id="new-password"
        class="input max-w-sm"
        v-model="password"
        type="password"
        minlength="1"
        maxlength="28"
        required
        autocomplete="new-password"
      />
      <p class="text-xs text-gray-400">
        1â€“28 printable characters, without spaces.
      </p>
      <div class="flex gap-2">
        <button class="btn-primary" :disabled="owner.busy || !password">
          Reset password</button
        ><button type="button" class="btn-ghost" @click="cancelPassword">
          Cancel
        </button>
      </div>
    </form>
    <label class="block text-sm" for="account-search">Find an account</label>
    <input
      id="account-search"
      class="input max-w-sm"
      v-model="search"
      placeholder="Account name"
      type="search"
    />
    <p v-if="loading" role="status">Loading accountsâ€¦</p>
    <p v-else-if="!visible.length" class="text-gray-400">
      No matching accounts.
    </p>
    <div v-else class="divide-y divide-gray-800 border-y border-gray-800">
      <article
        v-for="account in visible"
        :key="`${account.source_loginserver}:${account.id}`"
        class="py-4 flex flex-wrap items-center justify-between gap-3"
      >
        <div>
          <h2 class="font-semibold">{{ account.account_name }}</h2>
          <p class="text-xs text-gray-400">
            ID {{ account.id }} Â· {{ account.source_loginserver }}
          </p>
          <p class="text-xs text-gray-400 mt-1">
            Last login:
            {{
              account.last_login_date
                ? new Date(account.last_login_date).toLocaleString()
                : 'Never'
            }}
          </p>
        </div>
        <div class="flex gap-2">
          <button
            class="btn-blue"
            :disabled="owner.busy || account.source_loginserver !== 'local'"
            @click="selectAccount(account)"
          >
            Reset password</button
          ><button
            class="btn-red"
            :disabled="owner.busy || account.source_loginserver !== 'local'"
            @click="remove(account)"
          >
            Delete
          </button>
        </div>
      </article>
    </div>
    <p class="text-xs text-gray-400">
      Deletion requires maintenance and is blocked for accounts that own
      characters.
    </p>
  </section>
</template>

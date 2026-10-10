<template>
  <div class="flex flex-col md:flex-row min-h-screen">
    <!-- Sidebar -->
    <aside
      class="md:w-56 bg-gray-900 border-r border-gray-800 flex flex-col p-4 shrink-0"
    >
      <div class="mb-6 px-1">
        <div class="text-amber-400 font-bold text-lg leading-none">
          Nightcap GM
        </div>
        <div class="text-gray-400 text-xs mt-1">Owner controls</div>
        <label for="environment" class="block text-xs mt-5 mb-2 text-gray-300"
          >Environment</label
        >
        <select
          id="environment"
          class="select w-full"
          :value="owner.environment"
          :disabled="owner.busy || !!owner.uncertain"
          @change="switchTarget"
        >
          <option value="local">Local development</option>
          <option value="production">OVH production</option>
        </select>
      </div>

      <nav class="flex-1 space-y-0.5">
        <router-link to="/" class="nav-link">
          <span>⚔</span> Characters
        </router-link>
        <router-link to="/accounts" class="nav-link">
          <span>🔐</span> Accounts
        </router-link>
        <router-link to="/access" class="nav-link"
          ><span>🔑</span> Player access</router-link
        >
        <router-link to="/server" class="nav-link">
          <span>⚙</span> Server Tweaks
        </router-link>
        <router-link to="/expansion" class="nav-link">
          <span>🗓</span> Expansion Lock
        </router-link>
      </nav>

      <div class="mt-auto pt-4 border-t border-gray-800">
        <div class="text-gray-400 text-xs px-1">
          Runs on this computer.<br />Production connects through SSH.
        </div>
      </div>
    </aside>

    <!-- Main -->
    <main class="flex-1 min-w-0">
      <RuntimePanel :key="owner.epoch" />
      <fieldset :disabled="owner.busy || !!owner.uncertain" class="min-w-0">
        <router-view :key="`${owner.epoch}:${route.path}`" />
      </fieldset>
    </main>
  </div>

  <!-- Toast -->
  <Transition name="toast">
    <div
      v-if="toast.visible"
      role="status"
      :class="toast.ok ? 'toast-ok' : 'toast-err'"
    >
      {{ toast.message }}
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { reactive, provide } from 'vue'
import { useRoute } from 'vue-router'
import { owner, selectEnvironment, type Environment } from './api'
import RuntimePanel from './components/RuntimePanel.vue'
const route = useRoute()
function switchTarget(event: Event) {
  selectEnvironment((event.target as HTMLSelectElement).value as Environment)
  toast.visible = false
}

const toast = reactive({ visible: false, message: '', ok: true })
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(message: string, ok = true) {
  if (
    message.includes('canceled') ||
    message.includes('View changed') ||
    message.includes('Action cancelled')
  )
    return
  if (toastTimer) clearTimeout(toastTimer)
  toast.message = message
  toast.ok = ok
  toast.visible = true
  toastTimer = setTimeout(() => {
    toast.visible = false
  }, 3000)
}

provide('toast', showToast)
</script>

<style>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>

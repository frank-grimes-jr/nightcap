<template>
  <div class="flex min-h-screen">
    <!-- Sidebar -->
    <aside
      class="w-52 bg-gray-900 border-r border-gray-800 flex flex-col p-4 shrink-0"
    >
      <div class="mb-6 px-1">
        <div class="text-amber-400 font-bold text-lg leading-none">
          EQ Solo GM
        </div>
        <div class="text-gray-600 text-xs mt-1">Local Dev Tools</div>
      </div>

      <nav class="flex-1 space-y-0.5">
        <router-link to="/" class="nav-link">
          <span>⚔</span> Characters
        </router-link>
        <router-link to="/accounts" class="nav-link">
          <span>🔐</span> Accounts
        </router-link>
        <router-link to="/server" class="nav-link">
          <span>⚙</span> Server Tweaks
        </router-link>
        <router-link to="/expansion" class="nav-link">
          <span>🗓</span> Expansion Lock
        </router-link>
      </nav>

      <div class="mt-auto pt-4 border-t border-gray-800">
        <div class="text-gray-700 text-xs px-1">
          MariaDB :3307 · Spire :3000
        </div>
      </div>
    </aside>

    <!-- Main -->
    <main class="flex-1 overflow-auto">
      <router-view />
    </main>
  </div>

  <!-- Toast -->
  <Transition name="toast">
    <div v-if="toast.visible" :class="toast.ok ? 'toast-ok' : 'toast-err'">
      {{ toast.message }}
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { reactive, provide } from 'vue'

const toast = reactive({ visible: false, message: '', ok: true })
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(message: string, ok = true) {
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

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { pendingConfirmation, answerConfirmation } from '../confirmation'

const dialog = ref<HTMLDialogElement | null>(null)
watch(
  pendingConfirmation,
  (pending) => {
    if (pending) dialog.value?.showModal()
    else dialog.value?.close()
  },
  { flush: 'post' }
)
onUnmounted(() => answerConfirmation(false))
</script>

<template>
  <dialog
    ref="dialog"
    aria-labelledby="action-confirmation-title"
    aria-describedby="action-confirmation-detail"
    class="m-auto w-[calc(100%-2rem)] max-w-md rounded-xl border border-gray-600 bg-gray-900 p-6 text-gray-100 shadow-2xl backdrop:bg-black/70"
    @cancel.prevent="answerConfirmation(false)"
  >
    <form v-if="pendingConfirmation" @submit.prevent="answerConfirmation(true)">
      <p class="mb-3 text-sm font-semibold text-amber-400">
        {{ pendingConfirmation.environment }}
      </p>
      <h2 id="action-confirmation-title" class="text-xl font-semibold">
        {{ pendingConfirmation.action }}
      </h2>
      <div id="action-confirmation-detail" class="mt-3 space-y-2 text-gray-300">
        <p v-if="pendingConfirmation.subject">
          For {{ pendingConfirmation.subject }}
        </p>
        <p v-if="pendingConfirmation.detail">
          {{ pendingConfirmation.detail }}
        </p>
        <p>Confirm this action on {{ pendingConfirmation.environment }}.</p>
      </div>
      <div class="mt-6 flex justify-end gap-3">
        <button
          type="button"
          class="btn-ghost"
          autofocus
          @click="answerConfirmation(false)"
        >
          Cancel
        </button>
        <button type="submit" class="btn-primary">Confirm action</button>
      </div>
    </form>
  </dialog>
</template>

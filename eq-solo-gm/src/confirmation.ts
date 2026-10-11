import { shallowRef } from 'vue'

export type Confirmation = {
  action: string
  subject: string
  environment: string
  detail: string
}
export const pendingConfirmation = shallowRef<Confirmation | null>(null)
let respond: ((approved: boolean) => void) | undefined

export function requestConfirmation(confirmation: Confirmation) {
  if (respond) throw new Error('Finish the pending confirmation first')
  return new Promise<boolean>((resolve) => {
    respond = resolve
    pendingConfirmation.value = confirmation
  })
}

export function answerConfirmation(approved: boolean) {
  const resolve = respond
  respond = undefined
  pendingConfirmation.value = null
  resolve?.(approved)
}

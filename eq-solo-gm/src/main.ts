import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import CharacterManager from './views/CharacterManager.vue'
import AccountManager from './views/AccountManager.vue'
import ServerTweaks from './views/ServerTweaks.vue'
import ExpansionLock from './views/ExpansionLock.vue'
import PlayerAccess from './views/PlayerAccess.vue'
import { owner } from './api'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/access',
      component: PlayerAccess,
      meta: { title: 'Player access' },
    },
    { path: '/', component: CharacterManager, meta: { title: 'Characters' } },
    {
      path: '/accounts',
      component: AccountManager,
      meta: { title: 'Accounts' },
    },
    {
      path: '/server',
      component: ServerTweaks,
      meta: { title: 'Server Tweaks' },
    },
    {
      path: '/expansion',
      component: ExpansionLock,
      meta: { title: 'Expansion Lock' },
    },
  ],
})

router.beforeEach(() => {
  if (owner.busy) return false
  owner.subject = ''
})

createApp(App).use(router).mount('#app')

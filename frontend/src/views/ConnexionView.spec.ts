/** Test de composant : rendu et remontée d'erreur de l'écran de connexion. */

import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ErreurHttp } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import ConnexionView from '@/views/ConnexionView.vue'

const pousser = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push: pousser }),
}))

describe('ConnexionView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('affiche le formulaire', () => {
    const vue = mount(ConnexionView)

    expect(vue.find('h1').text()).toBe('Connexion')
    expect(vue.find('input[type="email"]').exists()).toBe(true)
    expect(vue.find('input[type="password"]').exists()).toBe(true)
    expect(vue.find('button[type="submit"]').text()).toContain('Se connecter')
  })

  it('redirige après une connexion réussie', async () => {
    const store = useAuthStore()
    vi.spyOn(store, 'connexion').mockResolvedValue(undefined)

    const vue = mount(ConnexionView)
    await vue.find('input[type="email"]').setValue('claire@example.com')
    await vue.find('input[type="password"]').setValue('MotDePasse')
    await vue.find('form').trigger('submit')

    expect(store.connexion).toHaveBeenCalledWith('claire@example.com', 'MotDePasse')
    expect(pousser).toHaveBeenCalledWith('/')
  })

  it("affiche le message d'erreur renvoyé par l'API", async () => {
    const store = useAuthStore()
    vi.spyOn(store, 'connexion').mockRejectedValue(
      new ErreurHttp(401, 'Adresse ou mot de passe incorrect.'),
    )

    const vue = mount(ConnexionView)
    await vue.find('form').trigger('submit')
    await vue.vm.$nextTick()

    const alerte = vue.find('[role="alert"]')
    expect(alerte.exists()).toBe(true)
    expect(alerte.text()).toBe('Adresse ou mot de passe incorrect.')
    expect(pousser).not.toHaveBeenCalled()
  })
})

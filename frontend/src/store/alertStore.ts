import { create } from 'zustand'

export interface Alert {
  id: number
  prediction_id: number
  tier: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED'
  recommended_action: string
  status: 'PENDING_VERIFICATION' | 'VERIFIED' | 'DISMISSED' | 'DOWNGRADED'
  created_at: string
  notes?: string
  causal_path?: CausalNode[]
  impact?: ImpactData
}

export interface CausalNode {
  node: string
  label: string
  probability: number
  state: 'LOW' | 'MEDIUM' | 'HIGH'
}

export interface ImpactData {
  impact_score: number
  population_exposed: number
  hospitals_exposed: number
  roads_affected_km: number
  shelters_available: number
  vulnerability_index: number
}

interface AlertStore {
  activeAlerts: Alert[]
  addAlert: (alert: Alert) => void
  updateAlertStatus: (id: number, status: Alert['status']) => void
  clearAlerts: () => void
}

const useAlertStore = create<AlertStore>((set) => ({
  activeAlerts: [],
  addAlert: (alert) =>
    set((s) => ({ activeAlerts: [alert, ...s.activeAlerts].slice(0, 50) })),
  updateAlertStatus: (id, status) =>
    set((s) => ({
      activeAlerts: s.activeAlerts.map((a) =>
        a.id === id ? { ...a, status } : a
      ),
    })),
  clearAlerts: () => set({ activeAlerts: [] }),
}))

export default useAlertStore

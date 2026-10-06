import { NavLink } from 'react-router-dom'
import { ReactNode } from 'react'
import { Activity, Map, RotateCcw, Shield, BookOpen, Waves } from 'lucide-react'
import useAlertStore from '../store/alertStore'

interface Props { children: ReactNode }

const NAV = [
  { to: '/',            icon: Waves,      label: 'Overview' },
  { to: '/dashboard',   icon: Map,        label: 'Live Dashboard' },
  { to: '/replay',      icon: RotateCcw,  label: 'Historical Replay' },
  { to: '/verify',      icon: Shield,     label: 'Verification Queue' },
  { to: '/methodology', icon: BookOpen,   label: 'Methodology' },
]

export default function AppShell({ children }: Props) {
  const { activeAlerts } = useAlertStore()
  const pendingCount = activeAlerts.filter(a => a.status === 'PENDING_VERIFICATION').length
  const highestTier = activeAlerts.reduce((t, a) => {
    const tiers = ['GREEN', 'YELLOW', 'ORANGE', 'RED']
    return tiers.indexOf(a.tier) > tiers.indexOf(t) ? a.tier : t
  }, 'GREEN')

  const tierColors: Record<string, string> = {
    GREEN: 'var(--green)', YELLOW: 'var(--yellow)',
    ORANGE: 'var(--orange)', RED: 'var(--red)',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* Top header */}
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 20px', height: '52px', flexShrink: 0,
        background: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border)',
        zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: 32, height: 32, borderRadius: '8px',
            background: 'linear-gradient(135deg, var(--teal), #0070a8)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Activity size={18} color="white" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '15px', letterSpacing: '-0.02em' }}>
              CascadeIQ
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Multi-Hazard Cascade Intelligence
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {pendingCount > 0 && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '4px 12px', borderRadius: '100px',
              background: `${tierColors[highestTier]}18`,
              border: `1px solid ${tierColors[highestTier]}40`,
              color: tierColors[highestTier],
              fontSize: '12px', fontWeight: 600,
              animation: highestTier === 'RED' ? 'pulse-red 1.5s ease-in-out infinite' : undefined,
            }}>
              <span style={{
                width: 8, height: 8, borderRadius: '50%',
                background: tierColors[highestTier],
                display: 'inline-block',
              }} />
              {pendingCount} PENDING {highestTier}
            </div>
          )}
          <div className="data-disclaimer">
            ⚠ MVP · Pilot Region · Sikkim
          </div>
          <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
            v0.1.0
          </div>
        </div>
      </header>

      {/* Body */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar nav */}
        <nav style={{
          width: '180px', flexShrink: 0,
          padding: '12px 8px',
          background: 'var(--bg-surface)',
          borderRight: '1px solid var(--border)',
          display: 'flex', flexDirection: 'column', gap: '4px',
          overflowY: 'auto',
        }}>
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to} to={to}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
              end={to === '/'}
            >
              <Icon size={15} />
              <span>{label}</span>
            </NavLink>
          ))}

          <div style={{ marginTop: 'auto', paddingTop: '16px' }}>
            <div style={{
              padding: '10px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
            }}>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
                Pilot Region
              </div>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--teal)' }}>
                Sikkim — Teesta Valley
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Hazard pair: Rainfall → Landslide → Blockage → Flood
              </div>
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main style={{ flex: 1, overflow: 'auto', position: 'relative' }}>
          {children}
        </main>
      </div>
    </div>
  )
}

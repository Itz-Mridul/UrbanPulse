interface Props {
  tier: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED'
  probability: number
  impact_score?: number
  large?: boolean
}

const TIER_CONFIG = {
  GREEN:  { color: 'var(--green)',  dim: 'var(--green-dim)',  icon: '✓',  label: 'NORMAL',  desc: 'No cascade trigger detected' },
  YELLOW: { color: 'var(--yellow)', dim: 'var(--yellow-dim)', icon: '👁', label: 'WATCH',   desc: 'Elevated cascade risk' },
  ORANGE: { color: 'var(--orange)', dim: 'var(--orange-dim)', icon: '⚠', label: 'ADVISORY', desc: 'Pre-position resources' },
  RED:    { color: 'var(--red)',    dim: 'var(--red-dim)',    icon: '🚨', label: 'IMMEDIATE', desc: 'Evacuation order required' },
}

export default function TierBadge({ tier, probability, impact_score, large }: Props) {
  const cfg = TIER_CONFIG[tier]
  const pulse = tier === 'RED' ? 'pulse-red' : tier === 'ORANGE' ? 'pulse-orange' : ''

  return (
    <div style={{
      display: 'inline-flex', flexDirection: 'column', alignItems: 'center',
      gap: large ? '8px' : '4px',
    }}>
      <div
        className={pulse}
        role="status"
        aria-label={`Alert tier: ${cfg.label}`}
        style={{
          display: 'flex', alignItems: 'center', gap: large ? '10px' : '6px',
          padding: large ? '10px 20px' : '4px 12px',
          borderRadius: '100px',
          background: cfg.dim,
          border: `1px solid ${cfg.color}40`,
          color: cfg.color,
          fontWeight: 700,
          fontSize: large ? '18px' : '12px',
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
        }}
      >
        <span aria-hidden="true">{cfg.icon}</span>
        <span>{cfg.label}</span>
      </div>
      {large && (
        <>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '28px', fontWeight: 800, color: cfg.color }}>
            {(probability * 100).toFixed(1)}%
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            {cfg.desc}
          </div>
          {impact_score !== undefined && (
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Impact Score: <span style={{ fontFamily: 'var(--font-mono)', color: cfg.color }}>{impact_score.toFixed(1)}</span>/100
            </div>
          )}
        </>
      )}
    </div>
  )
}

import { CausalNode } from '../store/alertStore'

interface Props {
  nodes: CausalNode[]
  compact?: boolean
}

const STATE_COLORS: Record<string, string> = {
  LOW:    'var(--green)',
  MEDIUM: 'var(--yellow)',
  HIGH:   'var(--red)',
}

const NODE_ICONS: Record<string, string> = {
  Rainfall:            '🌧',
  SoilSaturation:      '💧',
  LandslideProbability:'⛰',
  RiverBlockage:       '🪨',
  DownstreamFlood:     '🌊',
}

export default function CausalChain({ nodes, compact = false }: Props) {
  if (!nodes?.length) return null

  return (
    <div>
      <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '10px' }}>
        Causal Path — Explainability
      </div>
      <div className="causal-chain" style={{ flexWrap: compact ? 'nowrap' : 'wrap', gap: '0', overflowX: 'auto', paddingBottom: '4px' }}>
        {nodes.map((node, i) => (
          <>
            <div key={node.node} className="causal-node" style={{
              borderColor: node.state === 'HIGH' ? 'var(--red)50' : node.state === 'MEDIUM' ? 'var(--yellow)50' : 'var(--border)',
              background: node.state === 'HIGH'
                ? 'rgba(239,68,68,0.06)'
                : node.state === 'MEDIUM'
                ? 'rgba(234,179,8,0.06)'
                : 'var(--bg-elevated)',
            }}>
              <span style={{ fontSize: compact ? '16px' : '20px' }}>{NODE_ICONS[node.node] || '🔷'}</span>
              <div className="causal-node-prob" style={{ color: STATE_COLORS[node.state], fontSize: compact ? '13px' : '15px' }}>
                {(node.probability * 100).toFixed(0)}%
              </div>
              <div className="causal-node-label" style={{ fontSize: compact ? '9px' : '10px' }}>
                {node.label.replace(/ Probability| Trigger/, '')}
              </div>
              <div style={{
                width: 6, height: 6, borderRadius: '50%',
                background: STATE_COLORS[node.state],
                marginTop: 2,
                boxShadow: `0 0 6px ${STATE_COLORS[node.state]}80`,
              }} aria-label={`State: ${node.state}`} />
            </div>
            {i < nodes.length - 1 && (
              <div className="causal-arrow" key={`arrow-${i}`} aria-hidden="true">→</div>
            )}
          </>
        ))}
      </div>
      <div style={{ marginTop: '8px', fontSize: '10px', color: 'var(--text-muted)' }}>
        🟢 Low &nbsp; 🟡 Medium &nbsp; 🔴 High — probability of each cascade trigger
      </div>
    </div>
  )
}

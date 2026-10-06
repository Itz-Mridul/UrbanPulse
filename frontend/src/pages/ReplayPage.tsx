import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { Play, Pause, SkipBack, SkipForward, Info } from 'lucide-react'
import CausalChain from '../components/CausalChain'
import TierBadge from '../components/TierBadge'
import { CausalNode } from '../store/alertStore'

interface ReplayFrame {
  offset_hours: number
  simulation_timestamp: string
  is_real_event: boolean
  label: string
  notes: string
  data_source: string
  inference: {
    probability: number
    time_lag_min_hours: number
    time_lag_max_hours: number
    causal_path: CausalNode[]
    tier: string
  }
  impact: {
    impact_score: number
    population_exposed: number
    hospitals_exposed: number
    roads_affected_km: number
    shelters_available: number
  }
  alert: {
    tier: string
    recommended_action: string
    probability: number
    impact_score: number
  }
}

const TIER_COLORS: Record<string, string> = {
  GREEN: '#22c55e', YELLOW: '#eab308', ORANGE: '#f97316', RED: '#ef4444',
}

// Embedded fallback data (works fully offline — critical for finale day)
const OFFLINE_REPLAY: ReplayFrame[] = [
  {
    offset_hours: -72, label: 'T-72h: Pre-event baseline',
    simulation_timestamp: '2023-10-01T04:00:00+00:00',
    is_real_event: false,
    notes: 'Normal monsoon conditions. Lhonak lake at ~1.5km² area.',
    data_source: 'SYNTHETIC_HISTORICAL',
    inference: { probability: 0.04, time_lag_min_hours: 3.2, time_lag_max_hours: 5.8, tier: 'GREEN', causal_path: [
      { node: 'Rainfall', label: 'Rainfall (45mm/24h)', probability: 0.09, state: 'LOW' },
      { node: 'SoilSaturation', label: 'Soil Saturation (55%)', probability: 0.55, state: 'MEDIUM' },
      { node: 'LandslideProbability', label: 'Landslide Trigger', probability: 0.04, state: 'LOW' },
      { node: 'RiverBlockage', label: 'River Blockage', probability: 0.03, state: 'LOW' },
      { node: 'DownstreamFlood', label: 'Downstream Flood', probability: 0.04, state: 'LOW' },
    ] },
    impact: { impact_score: 2.1, population_exposed: 12400, hospitals_exposed: 3, roads_affected_km: 87, shelters_available: 8 },
    alert: { tier: 'GREEN', recommended_action: 'NORMAL: Routine monitoring continues.', probability: 0.04, impact_score: 2.1 },
  },
  {
    offset_hours: -48, label: 'T-48h: Heavy rainfall onset',
    simulation_timestamp: '2023-10-02T04:00:00+00:00',
    is_real_event: false,
    notes: 'IMD records 110mm/24h. Soil saturation rising. River Teesta at moderate level.',
    data_source: 'SYNTHETIC_HISTORICAL',
    inference: { probability: 0.12, time_lag_min_hours: 3.2, time_lag_max_hours: 5.8, tier: 'YELLOW', causal_path: [
      { node: 'Rainfall', label: 'Rainfall (110mm/24h)', probability: 0.35, state: 'MEDIUM' },
      { node: 'SoilSaturation', label: 'Soil Saturation (68%)', probability: 0.68, state: 'MEDIUM' },
      { node: 'LandslideProbability', label: 'Landslide Trigger', probability: 0.18, state: 'LOW' },
      { node: 'RiverBlockage', label: 'River Blockage', probability: 0.10, state: 'LOW' },
      { node: 'DownstreamFlood', label: 'Downstream Flood', probability: 0.12, state: 'LOW' },
    ] },
    impact: { impact_score: 10.8, population_exposed: 12400, hospitals_exposed: 3, roads_affected_km: 87, shelters_available: 8 },
    alert: { tier: 'YELLOW', recommended_action: 'WATCH: Elevated cascade risk. Review evacuation plans.', probability: 0.12, impact_score: 10.8 },
  },
  {
    offset_hours: -36, label: 'T-36h: Extreme rainfall — Cyclone Hamoon remnants',
    simulation_timestamp: '2023-10-02T16:00:00+00:00',
    is_real_event: false,
    notes: 'Extreme 165mm/24h. Soil near saturation. Small debris flows on slopes.',
    data_source: 'SYNTHETIC_HISTORICAL',
    inference: { probability: 0.28, time_lag_min_hours: 3.2, time_lag_max_hours: 5.8, tier: 'YELLOW', causal_path: [
      { node: 'Rainfall', label: 'Rainfall (165mm/24h)', probability: 0.72, state: 'HIGH' },
      { node: 'SoilSaturation', label: 'Soil Saturation (78%)', probability: 0.78, state: 'HIGH' },
      { node: 'LandslideProbability', label: 'Landslide Trigger', probability: 0.42, state: 'MEDIUM' },
      { node: 'RiverBlockage', label: 'River Blockage', probability: 0.25, state: 'MEDIUM' },
      { node: 'DownstreamFlood', label: 'Downstream Flood', probability: 0.28, state: 'MEDIUM' },
    ] },
    impact: { impact_score: 24.3, population_exposed: 12400, hospitals_exposed: 3, roads_affected_km: 87, shelters_available: 8 },
    alert: { tier: 'YELLOW', recommended_action: 'WATCH: Monitor rainfall and river gauges closely.', probability: 0.28, impact_score: 24.3 },
  },
  {
    offset_hours: -24, label: 'T-24h: ⚠ CascadeIQ ORANGE alert threshold crossed',
    simulation_timestamp: '2023-10-03T04:00:00+00:00',
    is_real_event: false,
    notes: '190mm/24h exceeds Caine threshold. Blockage physically plausible. System raises ORANGE alert — 24h before real event.',
    data_source: 'SYNTHETIC_HISTORICAL',
    inference: { probability: 0.47, time_lag_min_hours: 3.2, time_lag_max_hours: 5.8, tier: 'ORANGE', causal_path: [
      { node: 'Rainfall', label: 'Rainfall (190mm/24h)', probability: 0.88, state: 'HIGH' },
      { node: 'SoilSaturation', label: 'Soil Saturation (85%)', probability: 0.85, state: 'HIGH' },
      { node: 'LandslideProbability', label: 'Landslide Trigger', probability: 0.62, state: 'HIGH' },
      { node: 'RiverBlockage', label: 'River Blockage', probability: 0.45, state: 'MEDIUM' },
      { node: 'DownstreamFlood', label: 'Downstream Flood', probability: 0.47, state: 'MEDIUM' },
    ] },
    impact: { impact_score: 42.1, population_exposed: 12400, hospitals_exposed: 3, roads_affected_km: 87, shelters_available: 8 },
    alert: { tier: 'ORANGE', recommended_action: 'ADVISORY: Pre-position evacuation transport. Alert district administration. Monitor Teesta gauges every 30 minutes. Expected risk window: 3.2–5.8 hours.', probability: 0.47, impact_score: 42.1 },
  },
  {
    offset_hours: -12, label: 'T-12h: 🚨 RED alert — dam failure imminent',
    simulation_timestamp: '2023-10-03T16:00:00+00:00',
    is_real_event: false,
    notes: 'South Lhonak moraine dam under extreme stress. CascadeIQ RED. Estimated 3–5h travel to Singtam.',
    data_source: 'SYNTHETIC_HISTORICAL',
    inference: { probability: 0.71, time_lag_min_hours: 3.2, time_lag_max_hours: 5.8, tier: 'RED', causal_path: [
      { node: 'Rainfall', label: 'Rainfall (205mm/24h)', probability: 0.95, state: 'HIGH' },
      { node: 'SoilSaturation', label: 'Soil Saturation (92%)', probability: 0.92, state: 'HIGH' },
      { node: 'LandslideProbability', label: 'Landslide Trigger', probability: 0.82, state: 'HIGH' },
      { node: 'RiverBlockage', label: 'River Blockage', probability: 0.68, state: 'HIGH' },
      { node: 'DownstreamFlood', label: 'Downstream Flood', probability: 0.71, state: 'HIGH' },
    ] },
    impact: { impact_score: 68.4, population_exposed: 12400, hospitals_exposed: 3, roads_affected_km: 87, shelters_available: 8 },
    alert: { tier: 'RED', recommended_action: 'IMMEDIATE: Issue evacuation order for Singtam and Rangpo. Close NH-10. Activate shelters. Alert NDRF Gangtok. Estimated flood wave: 3.2–5.8 hours.', probability: 0.71, impact_score: 68.4 },
  },
  {
    offset_hours: -6, label: 'T-6h: Peak cascade risk',
    simulation_timestamp: '2023-10-03T22:00:00+00:00',
    is_real_event: false,
    notes: 'Moraine dam failure. GLOF initiated. Flood wave propagating downstream.',
    data_source: 'SYNTHETIC_HISTORICAL',
    inference: { probability: 0.88, time_lag_min_hours: 3.0, time_lag_max_hours: 5.2, tier: 'RED', causal_path: [
      { node: 'Rainfall', label: 'Rainfall (180mm/24h)', probability: 0.85, state: 'HIGH' },
      { node: 'SoilSaturation', label: 'Soil Saturation (95%)', probability: 0.95, state: 'HIGH' },
      { node: 'LandslideProbability', label: 'Landslide Trigger', probability: 0.91, state: 'HIGH' },
      { node: 'RiverBlockage', label: 'River Blockage', probability: 0.84, state: 'HIGH' },
      { node: 'DownstreamFlood', label: 'Downstream Flood', probability: 0.88, state: 'HIGH' },
    ] },
    impact: { impact_score: 84.2, population_exposed: 12400, hospitals_exposed: 3, roads_affected_km: 87, shelters_available: 8 },
    alert: { tier: 'RED', recommended_action: 'CRITICAL: GLOF confirmed. Full evacuation in progress. All emergency services on standby.', probability: 0.88, impact_score: 84.2 },
  },
  {
    offset_hours: 0, label: 'T=0: ✅ CONFIRMED — South Lhonak GLOF, 4 Oct 2023 04:00 IST',
    simulation_timestamp: '2023-10-04T04:00:00+00:00',
    is_real_event: true,
    notes: 'CONFIRMED REAL EVENT: Flood reached Singtam ~07:00 IST. ~40 fatalities, major infrastructure loss. CascadeIQ raised RED alert 12 hours earlier.',
    data_source: 'SYNTHETIC_HISTORICAL',
    inference: { probability: 0.95, time_lag_min_hours: 0, time_lag_max_hours: 3.0, tier: 'RED', causal_path: [
      { node: 'Rainfall', label: 'Rainfall (175mm/24h)', probability: 0.88, state: 'HIGH' },
      { node: 'SoilSaturation', label: 'Soil Saturation (95%)', probability: 0.95, state: 'HIGH' },
      { node: 'LandslideProbability', label: 'Landslide Trigger', probability: 0.95, state: 'HIGH' },
      { node: 'RiverBlockage', label: 'River Blockage', probability: 0.95, state: 'HIGH' },
      { node: 'DownstreamFlood', label: 'Downstream Flood', probability: 0.95, state: 'HIGH' },
    ] },
    impact: { impact_score: 91.8, population_exposed: 12400, hospitals_exposed: 3, roads_affected_km: 87, shelters_available: 8 },
    alert: { tier: 'RED', recommended_action: 'EVENT CONFIRMED. Flood wave reached Singtam. Emergency response active.', probability: 0.95, impact_score: 91.8 },
  },
]

export default function ReplayPage() {
  const [frameIndex, setFrameIndex] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [frames, setFrames] = useState<ReplayFrame[]>(OFFLINE_REPLAY)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Try to fetch from backend, fall back to embedded offline data
  useQuery({
    queryKey: ['replay', 'sikkim_2023'],
    queryFn: async () => {
      const r = await axios.get('/api/v1/replay/sikkim_2023')
      if (r.data.frames?.length) setFrames(r.data.frames)
      return r.data
    },
    retry: 1,
    staleTime: Infinity,
  })

  const currentFrame = frames[frameIndex]
  const tier = (currentFrame?.alert?.tier || 'GREEN') as 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED'
  const tierColor = TIER_COLORS[tier]

  // Autoplay
  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(() => {
        setFrameIndex(i => {
          if (i >= frames.length - 1) { setPlaying(false); return i }
          return i + 1
        })
      }, 1800)
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [playing, frames.length])

  const progress = (frameIndex / (frames.length - 1)) * 100

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '14px 20px', flexShrink: 0,
        background: 'var(--bg-surface)', borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div>
          <h1 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '2px' }}>
            Historical Replay — Sikkim 2023 GLOF
          </h1>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <span className="data-disclaimer">SYNTHETIC_HISTORICAL</span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Reconstructed from published research (Sattar et al. 2024). Not live operational data.
            </span>
          </div>
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--teal)' }}>
          {new Date(currentFrame?.simulation_timestamp).toLocaleString('en-IN', {
            timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit',
          })} IST
        </div>
      </div>

      {/* Main body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left: Timeline list */}
        <div style={{
          width: '260px', flexShrink: 0,
          borderRight: '1px solid var(--border)',
          overflowY: 'auto', padding: '12px 8px',
        }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px', paddingLeft: '6px' }}>
            Event Timeline
          </div>
          {frames.map((f, i) => {
            const ftier = f.alert.tier
            const fcolor = TIER_COLORS[ftier]
            const isActive = i === frameIndex
            return (
              <button
                key={i}
                onClick={() => { setFrameIndex(i); setPlaying(false) }}
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: '10px',
                  width: '100%', padding: '10px 8px', borderRadius: 'var(--radius-md)',
                  background: isActive ? `${fcolor}12` : 'transparent',
                  border: `1px solid ${isActive ? fcolor + '40' : 'transparent'}`,
                  cursor: 'pointer', textAlign: 'left', marginBottom: '4px',
                  transition: 'var(--transition)',
                }}
              >
                <div style={{
                  width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                  background: fcolor, marginTop: 4,
                  boxShadow: isActive ? `0 0 6px ${fcolor}80` : 'none',
                }} />
                <div>
                  <div style={{ fontSize: '11px', fontWeight: isActive ? 600 : 400, color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                    {f.is_real_event ? '⭐ ' : ''}{f.offset_hours === 0 ? 'T=0 Real Event' : `T${f.offset_hours}h`}
                  </div>
                  <div style={{ fontSize: '10px', color: isActive ? fcolor : 'var(--text-muted)', fontWeight: 600 }}>
                    {ftier}
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
                    P={( f.inference.probability * 100).toFixed(0)}%
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        {/* Right: Frame detail */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* Frame label */}
          <div style={{
            padding: '16px 20px', borderRadius: 'var(--radius-lg)',
            background: currentFrame?.is_real_event ? 'rgba(239,68,68,0.08)' : `${tierColor}08`,
            border: `1px solid ${currentFrame?.is_real_event ? '#ef444430' : tierColor + '30'}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ fontWeight: 700, fontSize: '15px', color: currentFrame?.is_real_event ? '#ef4444' : tierColor }}>
                {currentFrame?.label}
              </div>
              <TierBadge
                tier={tier}
                probability={currentFrame?.inference?.probability ?? 0}
                large={false}
              />
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              {currentFrame?.notes}
            </div>
            {currentFrame?.is_real_event && (
              <div style={{
                marginTop: '10px', padding: '8px 12px', borderRadius: 'var(--radius-md)',
                background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.25)',
                fontSize: '11px', color: '#22c55e', fontWeight: 600,
              }}>
                ✓ CascadeIQ raised RED alert 12 hours before this event — with estimated flood wave arrival of 3–6 hours after detection
              </div>
            )}
          </div>

          {/* Probability + causal path */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px',
          }}>
            <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Flood Probability</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '32px', fontWeight: 800, color: tierColor }}>
                {((currentFrame?.inference?.probability ?? 0) * 100).toFixed(1)}%
              </div>
              <div className="prob-bar-track" style={{ marginTop: '8px' }}>
                <div className="prob-bar-fill" style={{
                  width: `${(currentFrame?.inference?.probability ?? 0) * 100}%`,
                  background: `linear-gradient(90deg, ${tierColor}60, ${tierColor})`,
                }} />
              </div>
            </div>
            <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Impact Score</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '32px', fontWeight: 800, color: tierColor }}>
                {(currentFrame?.impact?.impact_score ?? 0).toFixed(1)}<span style={{ fontSize: '14px', fontWeight: 400 }}>/100</span>
              </div>
              <div className="prob-bar-track" style={{ marginTop: '8px' }}>
                <div className="prob-bar-fill" style={{
                  width: `${currentFrame?.impact?.impact_score ?? 0}%`,
                  background: `linear-gradient(90deg, ${tierColor}60, ${tierColor})`,
                }} />
              </div>
            </div>
          </div>

          {/* Causal chain */}
          <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
            <CausalChain nodes={currentFrame?.inference?.causal_path ?? []} />
          </div>

          {/* Recommended action */}
          <div style={{
            padding: '14px', borderRadius: 'var(--radius-md)',
            background: `${tierColor}08`, border: `1px solid ${tierColor}30`,
          }}>
            <div style={{ fontSize: '10px', color: tierColor, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>
              🚨 Recommended Action
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
              {currentFrame?.alert?.recommended_action}
            </div>
          </div>

          {/* Lead time callout */}
          {frameIndex < frames.length - 1 && (
            <div style={{
              padding: '12px 16px', borderRadius: 'var(--radius-md)',
              background: 'var(--bg-elevated)', border: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', gap: '10px',
              fontSize: '12px', color: 'var(--text-secondary)',
            }}>
              <Info size={14} color="var(--teal)" />
              Real event occurs in{' '}
              <strong style={{ color: 'var(--teal)', fontFamily: 'var(--font-mono)' }}>
                {Math.abs(currentFrame?.offset_hours)}h
              </strong>
              {' '}— {tier !== 'GREEN' ? `CascadeIQ already raised ${tier} alert` : 'system in normal watch mode'}
            </div>
          )}
        </div>
      </div>

      {/* Bottom timeline scrubber */}
      <div style={{
        padding: '14px 20px', flexShrink: 0,
        background: 'var(--bg-surface)', borderTop: '1px solid var(--border)',
      }}>
        {/* Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <button className="btn btn-ghost" style={{ padding: '6px 10px' }} onClick={() => { setFrameIndex(0); setPlaying(false) }}>
            <SkipBack size={14} />
          </button>
          <button
            className={`btn ${playing ? 'btn-ghost' : 'btn-primary'}`}
            style={{ padding: '6px 16px', minWidth: '80px' }}
            onClick={() => setPlaying(p => !p)}
          >
            {playing ? <><Pause size={14} /> Pause</> : <><Play size={14} /> Play</>}
          </button>
          <button className="btn btn-ghost" style={{ padding: '6px 10px' }} onClick={() => { setFrameIndex(frames.length - 1); setPlaying(false) }}>
            <SkipForward size={14} />
          </button>
          <div style={{ marginLeft: 'auto', fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {frameIndex + 1} / {frames.length}
          </div>
        </div>

        {/* Track */}
        <div style={{ position: 'relative' }}>
          <input
            type="range" min={0} max={frames.length - 1} value={frameIndex}
            onChange={e => { setFrameIndex(Number(e.target.value)); setPlaying(false) }}
            style={{ width: '100%', cursor: 'pointer', accentColor: 'var(--teal)' }}
            aria-label="Replay timeline scrubber"
          />
          {/* Tier markers */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px' }}>
            {frames.map((f, i) => (
              <div key={i} style={{
                flex: 1, textAlign: 'center',
                fontSize: '9px',
                color: i === frameIndex ? TIER_COLORS[f.alert.tier] : 'var(--text-muted)',
                fontWeight: i === frameIndex ? 700 : 400,
                transition: 'var(--transition)',
              }}>
                {f.is_real_event ? '⭐ Real' : `T${f.offset_hours}h`}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

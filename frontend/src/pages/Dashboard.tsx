import { useEffect, useState, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { Users, Hospital, Route, ShieldCheck, Zap } from 'lucide-react'
import CausalChain from '../components/CausalChain'
import TierBadge from '../components/TierBadge'
import { useWebSocket } from '../hooks/useWebSocket'
import useAlertStore from '../store/alertStore'
import { CausalNode } from '../store/alertStore'

// Pilot region: Sikkim Teesta Valley
const MAP_CENTER: [number, number] = [18.5204, 73.8567] // Pune
const MAP_ZOOM = 12.5

// Hazard node positions on the map
const HAZARD_NODES = [
  { id: 'rainfall', label: 'Extreme Rainfall Zone', pos: [18.45, 73.78] as [number, number], color: '#60d4f7', radius: 3000 },
  { id: 'landslide', label: 'Landslide Risk (Sinhagad)', pos: [18.48, 73.82] as [number, number], color: '#eab308', radius: 2500 },
  { id: 'blockage', label: 'River Blockage Point', pos: [18.50, 73.84] as [number, number], color: '#f97316', radius: 2000 },
  { id: 'flood', label: 'Downstream Flood (Hadapsar)', pos: [18.52, 73.87] as [number, number], color: '#ef4444', radius: 4000 },
]

// Approximate downstream impact polygon (Teesta valley below Singtam)
const IMPACT_POLYGON: [number, number][] = [
  [27.22, 88.52], [27.22, 88.68], [27.10, 88.70], [27.05, 88.65],
  [27.05, 88.50], [27.10, 88.45], [27.22, 88.52],
]

// Fallback mock data for offline/demo mode
const MOCK_PREDICTION = {
  probability: 0.72,
  time_lag_min_hours: 3.2,
  time_lag_max_hours: 5.8,
  tier: 'RED' as const,
  causal_path: [
    { node: 'Rainfall', label: 'Rainfall (190mm/24h)', probability: 0.91, state: 'HIGH' as const },
    { node: 'SoilSaturation', label: 'Soil Saturation (85%)', probability: 0.85, state: 'HIGH' as const },
    { node: 'LandslideProbability', label: 'Landslide Trigger', probability: 0.78, state: 'HIGH' as const },
    { node: 'RiverBlockage', label: 'River Blockage', probability: 0.65, state: 'HIGH' as const },
    { node: 'DownstreamFlood', label: 'Downstream Flood', probability: 0.72, state: 'HIGH' as const },
  ] as CausalNode[],
  impact: {
    impact_score: 71.4,
    population_exposed: 12_400,
    hospitals_exposed: 3,
    roads_affected_km: 87,
    shelters_available: 8,
    vulnerability_index: 0.74,
  },
  recommended_action: 'IMMEDIATE: Issue evacuation order for downstream settlements in South Sikkim district between Singtam and Rangpo. Close NH-10 (Teesta riverside sections). Activate Rangpo Emergency Shelter (capacity 800). Alert SDMA Sikkim and notify NDRF team stationed at Gangtok. Estimated flood wave arrival: 3.2–5.8 hours.',
}

function TierColor(tier: string): string {
  const map: Record<string, string> = {
    GREEN: '#22c55e', YELLOW: '#eab308', ORANGE: '#f97316', RED: '#ef4444',
  }
  return map[tier] || '#22c55e'
}

export default function Dashboard() {
  useWebSocket() // Connect to real-time alert stream
  const { activeAlerts } = useAlertStore()
  const [useMockData, setUseMockData] = useState(false)

  // Fetch live prediction (falls back to mock)
  const { data: livePrediction } = useQuery({
    queryKey: ['predictions', 'current'],
    queryFn: async () => {
      const r = await axios.get('/api/v1/predictions/current?region_id=1')
      return r.data[0] ?? null
    },
    refetchInterval: 15_000,
    retry: 1,
    onError: () => setUseMockData(true),
  })

  const prediction = useMockData || !livePrediction ? MOCK_PREDICTION : livePrediction
  const tier = (prediction?.tier || 'GREEN') as 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED'
  const tierColor = TierColor(tier)
  const causalPath = prediction?.causal_path || MOCK_PREDICTION.causal_path
  const impact = prediction?.impact || MOCK_PREDICTION.impact

  
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const mapboxToken = import.meta.env.VITE_MAPBOX_TOKEN;
    if (!mapboxToken) {
      mapContainerRef.current.textContent = 'Set VITE_MAPBOX_TOKEN to display the map.';
      return;
    }
    mapboxgl.accessToken = mapboxToken;
    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/standard',
      center: [MAP_CENTER[1], MAP_CENTER[0]], // Mapbox expects [lng, lat]
      zoom: MAP_ZOOM,
      pitch: 60,
      bearing: -17.6,
      antialias: true
    });

    mapRef.current = map;

    map.on('style.load', () => {
      map.setConfigProperty('basemap', 'lightPreset', 'dusk');

      // Add hazard nodes as circles
      HAZARD_NODES.forEach((node) => {
        const sourceId = `hazard-source-${node.id}`;
        map.addSource(sourceId, {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: {},
            geometry: {
              type: 'Point',
              coordinates: [node.pos[1], node.pos[0]]
            }
          }
        });

        map.addLayer({
          id: `hazard-layer-${node.id}`,
          type: 'circle',
          source: sourceId,
          paint: {
            'circle-radius': node.radius / 100, // Approximate radius
            'circle-color': node.color,
            'circle-opacity': 0.4,
            'circle-stroke-width': 2,
            'circle-stroke-color': node.color
          }
        });
      });
    });

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* Left panel */}
      <div style={{
        width: '320px', flexShrink: 0,
        display: 'flex', flexDirection: 'column', gap: '12px',
        padding: '14px', overflowY: 'auto',
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--border)',
      }}>
        {/* Status header */}
        <div style={{
          padding: '16px', borderRadius: 'var(--radius-lg)',
          background: `${tierColor}08`,
          border: `1px solid ${tierColor}30`,
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px',
        }}>
          {useMockData && (
            <div className="data-disclaimer" style={{ marginBottom: '8px' }}>
              ⚠ Demo mode — mock data
            </div>
          )}
          <TierBadge
            tier={tier}
            probability={prediction?.probability ?? 0}
            impact_score={impact?.impact_score}
            large
          />
        </div>

        {/* Time lag */}
        <div style={{
          padding: '12px', borderRadius: 'var(--radius-md)',
          background: 'var(--bg-elevated)', border: '1px solid var(--border)',
        }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
            ⏱ Estimated Flood Wave Arrival
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '22px', fontWeight: 700, color: tierColor }}>
            {prediction?.time_lag_min_hours?.toFixed(1) ?? '?'}–{prediction?.time_lag_max_hours?.toFixed(1) ?? '?'}h
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            from blockage point to Singtam
          </div>
        </div>

        {/* Causal path */}
        <div style={{
          padding: '12px', borderRadius: 'var(--radius-md)',
          background: 'var(--bg-elevated)', border: '1px solid var(--border)',
        }}>
          <CausalChain nodes={causalPath} compact />
        </div>

        {/* Impact stats */}
        <div style={{
          padding: '12px', borderRadius: 'var(--radius-md)',
          background: 'var(--bg-elevated)', border: '1px solid var(--border)',
        }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>
            📊 Impact Exposure
          </div>
          <div className="impact-grid">
            <div className="impact-stat">
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
                <Users size={11} /> <span style={{ fontSize: '9px', textTransform: 'uppercase' }}>Population</span>
              </div>
              <div className="impact-stat-value" style={{ fontSize: '18px' }}>
                {impact?.population_exposed?.toLocaleString() ?? '—'}
              </div>
            </div>
            <div className="impact-stat">
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
                <Hospital size={11} /> <span style={{ fontSize: '9px', textTransform: 'uppercase' }}>Hospitals</span>
              </div>
              <div className="impact-stat-value" style={{ fontSize: '18px' }}>
                {impact?.hospitals_exposed ?? '—'}
              </div>
            </div>
            <div className="impact-stat">
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
                <Route size={11} /> <span style={{ fontSize: '9px', textTransform: 'uppercase' }}>Roads km</span>
              </div>
              <div className="impact-stat-value" style={{ fontSize: '18px' }}>
                {impact?.roads_affected_km ?? '—'}
              </div>
            </div>
            <div className="impact-stat">
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
                <ShieldCheck size={11} /> <span style={{ fontSize: '9px', textTransform: 'uppercase' }}>Shelters</span>
              </div>
              <div className="impact-stat-value" style={{ fontSize: '18px', color: 'var(--green)' }}>
                {impact?.shelters_available ?? '—'}
              </div>
            </div>
          </div>
          {/* Impact score bar */}
          <div style={{ marginTop: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Impact Score</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: tierColor }}>
                {impact?.impact_score?.toFixed(1) ?? '?'}/100
              </span>
            </div>
            <div className="prob-bar-track">
              <div className="prob-bar-fill" style={{
                width: `${impact?.impact_score ?? 0}%`,
                background: `linear-gradient(90deg, ${tierColor}80, ${tierColor})`,
              }} />
            </div>
          </div>
        </div>

        {/* Recommended action */}
        {prediction?.recommended_action && (
          <div style={{
            padding: '12px', borderRadius: 'var(--radius-md)',
            background: `${tierColor}08`,
            border: `1px solid ${tierColor}30`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', color: tierColor }}>
              <Zap size={12} />
              <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Recommended Action
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              {prediction.recommended_action}
            </div>
          </div>
        )}
      </div>

      {/* Map */}
      <div style={{ flex: 1, position: 'relative' }}>
        <div ref={mapContainerRef} style={{ width: '100%', height: '100%', borderRadius: '0.75rem', overflow: 'hidden' }} />

        {/* Map legend overlay */}
        <div style={{
          position: 'absolute', bottom: '20px', right: '10px', zIndex: 1000,
          padding: '10px 14px', borderRadius: 'var(--radius-md)',
          background: 'rgba(255,255,255,0.92)', backdropFilter: 'blur(8px)',
          border: '1px solid var(--border)',
          fontSize: '11px', minWidth: '160px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
        }}>
          <div style={{ fontWeight: 600, marginBottom: '8px', color: 'var(--teal)' }}>Cascade Chain</div>
          {HAZARD_NODES.map(n => (
            <div key={n.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', color: 'var(--text-secondary)' }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: n.color, flexShrink: 0 }} />
              {n.label.split(' (')[0]}
            </div>
          ))}
        </div>

        {/* Replay hint */}
        <div style={{
          position: 'absolute', top: '10px', left: '10px', zIndex: 1000,
          padding: '8px 12px', borderRadius: 'var(--radius-md)',
          background: 'rgba(255,255,255,0.92)', backdropFilter: 'blur(8px)',
          border: '1px solid var(--border)',
          fontSize: '11px', color: 'var(--text-secondary)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
        }}>
          🔴 Live monitoring — Teesta Valley, Sikkim<br />
          <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
            See <strong>Historical Replay</strong> for Sikkim 2023 backtest
          </span>
        </div>
      </div>
    </div>
  )
}

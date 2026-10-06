import { useNavigate } from 'react-router-dom'
import { Activity, Waves, Map, RotateCcw, Shield, ArrowRight, Zap } from 'lucide-react'

export default function LandingPage() {
  const nav = useNavigate()

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: '40px 32px' }}>
      <div style={{ maxWidth: '820px', margin: '0 auto' }}>
        {/* Hero */}
        <div style={{ textAlign: 'center', marginBottom: '52px' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '8px',
            padding: '6px 16px', borderRadius: '100px', marginBottom: '24px',
            background: 'var(--teal-dim)', border: '1px solid rgba(0,201,228,0.25)',
            fontSize: '12px', color: 'var(--teal)', fontWeight: 600, letterSpacing: '0.05em',
          }}>
            <Activity size={13} /> Indradhanu · PCCOE International Grand Challenge 2026
          </div>

          <h1 style={{
            fontSize: '48px', fontWeight: 800, lineHeight: 1.15,
            background: 'linear-gradient(135deg, var(--text-primary) 40%, var(--teal))',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            backgroundClip: 'text', marginBottom: '20px',
          }}>
            CascadeIQ
          </h1>
          <p style={{ fontSize: '18px', color: 'var(--text-secondary)', lineHeight: 1.7, maxWidth: '560px', margin: '0 auto 12px' }}>
            AI for Cascading Hazard Impact &amp; Response — the connector layer that links India's existing single-hazard forecasts into multi-hazard cascade predictions.
          </p>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '32px' }}>
            Domain: Disaster Resilience, Public Health &amp; Community Well-being
          </p>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              id="goto-dashboard"
              className="btn btn-primary"
              style={{ padding: '11px 24px', fontSize: '14px' }}
              onClick={() => nav('/dashboard')}
            >
              <Map size={16} /> Live Dashboard <ArrowRight size={14} />
            </button>
            <button
              id="goto-replay"
              className="btn btn-ghost"
              style={{ padding: '11px 24px', fontSize: '14px' }}
              onClick={() => nav('/replay')}
            >
              <RotateCcw size={16} /> Sikkim 2023 Replay
            </button>
          </div>
        </div>

        {/* The gap */}
        <div style={{
          padding: '24px', borderRadius: 'var(--radius-xl)', marginBottom: '36px',
          background: 'var(--bg-surface)', border: '1px solid var(--border)',
        }}>
          <div style={{ fontSize: '12px', color: 'var(--teal)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '12px' }}>
            The Problem
          </div>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.8 }}>
            A village with a working local flood-warning system can still be blindsided by a flash flood caused by a landslide-dam burst 20 km upstream — because the local model only watches local rainfall, with no input channel for "a landslide just blocked the river upstream." <strong style={{ color: 'var(--text-primary)' }}>Existing single-hazard systems don't talk to each other.</strong> This is an integration gap, not a knowledge gap.
          </p>
        </div>

        {/* Cascade chain visual */}
        <div style={{ marginBottom: '36px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '16px', textAlign: 'center' }}>
            Causal Chain — Rain-triggered GLOF cascade (Sikkim 2023)
          </div>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0',
            alignItems: 'center',
          }}>
            {[
              { icon: '🌧', label: 'Heavy Rainfall', desc: '190mm/24h', color: '#60d4f7' },
              null,
              { icon: '⛰', label: 'Landslide / GLOF', desc: 'Debris flow or moraine failure', color: '#eab308' },
              null,
              { icon: '🪨', label: 'River Blockage', desc: 'Temporary dam', color: '#f97316' },
              null,
              { icon: '🌊', label: 'Downstream Flood', desc: 'Singtam, 45km away', color: '#ef4444' },
            ].map((item, i) => {
              if (item === null) {
                return <div key={i} style={{ textAlign: 'center', fontSize: '20px', color: 'var(--text-muted)' }}>→</div>
              }
              return (
                <div key={i} style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px',
                  padding: '16px 8px', borderRadius: 'var(--radius-lg)',
                  background: `${item.color}10`, border: `1px solid ${item.color}30`,
                }}>
                  <span style={{ fontSize: '28px' }}>{item.icon}</span>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: item.color, textAlign: 'center' }}>{item.label}</div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', textAlign: 'center' }}>{item.desc}</div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Feature cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px', marginBottom: '36px' }}>
          {[
            {
              icon: <Waves size={18} color="var(--teal)" />,
              title: 'Bayesian Cascade Engine',
              desc: 'Physics-constrained Bayesian network (pgmpy) computing P(Flood | Landslide, terrain, river state) with an explicit time-lag window and full causal path.',
            },
            {
              icon: <Zap size={18} color="var(--yellow)" />,
              title: 'Physics + AI Hybrid',
              desc: 'Physics equations (Korup, Caine, Huss) define causal structure; the AI calibrates probabilities. Never a black box — every alert shows its causal chain.',
            },
            {
              icon: <Map size={18} color="var(--orange)" />,
              title: 'Impact Layer',
              desc: 'OSM overlay of hospitals, roads, shelters, and population. Impact Score = P × Exposure × Vulnerability. Who is at risk, specifically.',
            },
            {
              icon: <Shield size={18} color="var(--green)" />,
              title: 'Human-in-the-Loop',
              desc: 'No alert reaches public status without an authority officer verifying it. Tiered GREEN/YELLOW/ORANGE/RED with specific recommended actions per region.',
            },
          ].map(card => (
            <div key={card.title} style={{
              padding: '20px', borderRadius: 'var(--radius-lg)',
              background: 'var(--bg-surface)', border: '1px solid var(--border)',
              transition: 'var(--transition)',
            }}>
              <div style={{ marginBottom: '10px' }}>{card.icon}</div>
              <div style={{ fontWeight: 600, marginBottom: '6px', fontSize: '14px' }}>{card.title}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.7 }}>{card.desc}</div>
            </div>
          ))}
        </div>

        {/* MVP disclaimer */}
        <div style={{
          padding: '16px 20px', borderRadius: 'var(--radius-lg)',
          background: 'var(--amber-dim)', border: '1px solid rgba(245,158,11,0.25)',
          fontSize: '12px', color: 'var(--amber)', lineHeight: 1.7,
        }}>
          <strong>⚠ Scope Honesty (we say this first, always):</strong> This is a hackathon MVP — one hazard pair (rainfall → landslide → blockage → flood), one pilot region (Sikkim/Teesta Valley), backtested against Sikkim 2023 using synthetic historical reconstruction. Not national coverage. Not replacing IMD/GSI/CWC. Not addressing Wayanad-type warning-to-action gaps — that's a different system.
        </div>
      </div>
    </div>
  )
}

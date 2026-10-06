export default function MethodologyPage() {
  const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div style={{ marginBottom: '32px' }}>
      <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--teal)', marginBottom: '12px', paddingBottom: '8px', borderBottom: '1px solid var(--border)' }}>
        {title}
      </h2>
      {children}
    </div>
  )

  const P = ({ children }: { children: React.ReactNode }) => (
    <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.8', marginBottom: '10px' }}>{children}</p>
  )

  const Note = ({ children }: { children: React.ReactNode }) => (
    <div style={{
      padding: '12px 16px', borderRadius: 'var(--radius-md)', marginBottom: '12px',
      background: 'var(--amber-dim)', border: '1px solid rgba(245,158,11,0.25)',
      fontSize: '12px', color: 'var(--amber)', lineHeight: '1.7',
    }}>⚠ {children}</div>
  )

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: '28px 32px' }}>
      <div style={{ maxWidth: '720px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 800, marginBottom: '6px' }}>Methodology</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '32px' }}>
          Physics + AI hybrid approach for multi-hazard cascade prediction
        </p>

        <Note>
          CascadeIQ is an MVP for the Indradhanu PCCOE 2026 hackathon. It covers one hazard pair (rainfall → landslide → river blockage → downstream flood) in one pilot region (Sikkim/Teesta Valley). See the Non-Goals section before drawing production-scale conclusions.
        </Note>

        <Section title="1. The Gap We're Closing">
          <P>
            India's disaster agencies (IMD, GSI, CWC) already forecast individual hazards well. CascadeIQ is a <strong style={{ color: 'var(--text-primary)' }}>connector layer, not a competing predictor</strong>. It ingests those existing forecasts and computes the live probability that one hazard triggers a second, unrelated-looking hazard downstream — closing the integration gap, not replicating existing forecasts.
          </P>
          <P>
            Research context: 55% of AI early-warning literature focuses on forecasting; only 1% addresses response preparedness; only 4 of 324 reviewed multi-hazard papers model hazards as causal chains rather than independent events.
          </P>
        </Section>

        <Section title="2. Physics + AI Split (the key architectural decision)">
          <P>
            The system maintains a strict separation between physics-based constraints and learned probabilities:
          </P>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
            <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-elevated)', border: '1px solid var(--teal)30' }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--teal)', marginBottom: '8px', textTransform: 'uppercase' }}>Physics Module</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
                <strong>Defines causal structure</strong> and physical plausibility constraints:<br />
                • Korup (2002) dam-blockage threshold<br />
                • Caine (1980) rainfall trigger threshold (Himalayan-calibrated)<br />
                • Kinematic wave flood travel time (Huss et al. 2007)<br /><br />
                Pure functions — no learned parameters.
              </div>
            </div>
            <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-elevated)', border: '1px solid var(--amber)30' }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--amber)', marginBottom: '8px', textTransform: 'uppercase' }}>Bayesian Network (AI)</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
                <strong>Calibrates probabilities</strong> on top of the physics-constrained structure:<br />
                • pgmpy BayesianNetwork (DAG)<br />
                • Nodes: Rainfall, SoilSaturation, Slope, LandslideProbability, RiverBlockage, DownstreamFlood<br />
                • CPDs: physics-informed priors, updatable from historical data<br />
                • Variable Elimination for exact inference
              </div>
            </div>
          </div>
          <P>
            This split means the AI never invents physical relationships it was never shown. The causal structure is physics-constrained; only the probability calibration is learned.
          </P>
        </Section>

        <Section title="3. Impact Layer">
          <P>
            Given a predicted downstream impact zone, the Impact Layer overlays:
          </P>
          <ul style={{ paddingLeft: '20px', marginBottom: '10px' }}>
            {[
              'Population density (Census/LGD district-level data for pilot region)',
              'Hospitals and clinics (OpenStreetMap Overpass API — free, no key needed)',
              'Primary/secondary roads (OSM)',
              'Emergency shelters (OSM)',
            ].map(item => (
              <li key={item} style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px', lineHeight: '1.6' }}>{item}</li>
            ))}
          </ul>
          <P>
            Impact Score = 100 × P(flood) × (Exposure × 0.6 + Vulnerability × 0.4), where Vulnerability is the inverse of shelter coverage.
          </P>
        </Section>

        <Section title="4. Alert Tiers">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '12px' }}>
            {[
              { tier: 'GREEN',  icon: '✓', label: 'Normal',   p: '<15%',  desc: 'Routine monitoring' },
              { tier: 'YELLOW', icon: '👁', label: 'Watch',    p: '15–40%', desc: 'Review evacuation plans' },
              { tier: 'ORANGE', icon: '⚠', label: 'Advisory', p: '40–65%', desc: 'Pre-position resources' },
              { tier: 'RED',    icon: '🚨', label: 'Immediate',p: '>65%',  desc: 'Evacuation order' },
            ].map(t => {
              const colors: Record<string, string> = { GREEN: '#22c55e', YELLOW: '#eab308', ORANGE: '#f97316', RED: '#ef4444' }
              const c = colors[t.tier]
              return (
                <div key={t.tier} style={{ padding: '12px', borderRadius: 'var(--radius-md)', background: `${c}10`, border: `1px solid ${c}30`, textAlign: 'center' }}>
                  <div style={{ fontSize: '18px', marginBottom: '4px' }}>{t.icon}</div>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: c, marginBottom: '4px' }}>{t.label}</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>{t.p}</div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{t.desc}</div>
                </div>
              )
            })}
          </div>
          <P>Tiers are distinguished by color + icon + text label — colorblind-safe design.</P>
        </Section>

        <Section title="5. Human-in-the-Loop">
          <P>
            No alert reaches "public" status without an authority officer clicking Verify in the Verification Queue. This is a core design constraint, not an afterthought — it prevents false alarms from automatically triggering evacuations and maintains accountability. The feedback loop allows downgrading of predictions when new sensor data (e.g., river level stabilisation) contradicts the prior prediction.
          </P>
        </Section>

        <Section title="6. Backtest — Sikkim 2023">
          <P>
            The historical replay reconstructs the pre-event data leading up to the South Lhonak GLOF (4 October 2023) using published research data (Sattar et al. 2024). The replay shows CascadeIQ raising ORANGE alert at T-24h and RED at T-12h — with estimated flood wave arrival of 3–6h from blockage to Singtam.
          </P>
          <Note>
            This is a <strong>synthetic reconstruction</strong> from published research, labeled SYNTHETIC_HISTORICAL throughout the system. It demonstrates what CascadeIQ would have predicted given the pre-event data — it is not a real-time retrospective from live sensors.
          </Note>
        </Section>

        <Section title="7. Explicit Non-Goals">
          <ul style={{ paddingLeft: '20px' }}>
            {[
              'Not a replacement for IMD/GSI/CWC forecasts — it is a connector layer on top of them.',
              'Not addressing warning-to-action failures like Wayanad 2024 — that is a different system (community mobilisation, not hazard detection).',
              'Not a national, production-grade, always-on system — one hazard pair, one pilot region.',
              'Not doing individual-level health prediction.',
            ].map(item => (
              <li key={item} style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px', lineHeight: '1.6' }}>{item}</li>
            ))}
          </ul>
        </Section>

        <Section title="8. References">
          <ul style={{ paddingLeft: '20px' }}>
            {[
              'Caine, N. (1980). The rainfall intensity-duration control of shallow landslides and debris flows.',
              'Korup, O. (2002). Landslide-induced river channel avulsions in mountain catchments.',
              'Huss, M. et al. (2007). Modelling runoff from highly glacierized alpine drainage basins.',
              'Sattar, A. et al. (2024). South Lhonak lake outburst flood, Sikkim, October 2023.',
              'Papathoma-Köhle, M. et al. (2019). Physical vulnerability to landslides.',
              'pgmpy — Python library for Bayesian Networks and Probabilistic Graphical Models.',
            ].map(ref => (
              <li key={ref} style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px', lineHeight: '1.6' }}>{ref}</li>
            ))}
          </ul>
        </Section>
      </div>
    </div>
  )
}

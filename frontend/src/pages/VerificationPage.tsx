import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { ShieldCheck, ShieldX, Clock, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'
import TierBadge from '../components/TierBadge'

interface Alert {
  id: number
  prediction_id: number
  tier: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED'
  recommended_action: string
  status: string
  verified_by?: string
  verified_at?: string
  created_at: string
  notes?: string
}

const TIER_ICONS: Record<string, string> = {
  GREEN: '✓', YELLOW: '👁', ORANGE: '⚠', RED: '🚨',
}

export default function VerificationPage() {
  const qc = useQueryClient()
  const [token, setToken] = useState(localStorage.getItem('cascadeiq_token') || '')
  const [loginUser, setLoginUser] = useState('')
  const [loginPass, setLoginPass] = useState('')
  const [loginError, setLoginError] = useState('')
  const [notes, setNotes] = useState<Record<number, string>>({})

  const { data: alerts = [], isLoading } = useQuery<Alert[]>({
    queryKey: ['alerts'],
    queryFn: async () => {
      const r = await axios.get('/api/v1/alerts')
      return r.data
    },
    refetchInterval: 10_000,
    retry: 1,
  })

  const loginMutation = useMutation({
    mutationFn: async () => {
      const form = new URLSearchParams()
      form.append('username', loginUser)
      form.append('password', loginPass)
      const r = await axios.post('/api/v1/auth/token', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      return r.data.access_token
    },
    onSuccess: (t: string) => {
      setToken(t)
      localStorage.setItem('cascadeiq_token', t)
      setLoginError('')
    },
    onError: () => setLoginError('Invalid credentials. Check the account configured for this deployment.'),
  })

  const verifyMutation = useMutation({
    mutationFn: async ({ id, action, note }: { id: number; action: string; note?: string }) => {
      await axios.post(
        `/api/v1/alerts/${id}/verify`,
        { action, notes: note },
        { headers: { Authorization: `Bearer ${token}` } },
      )
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
    onError: (e: any) => {
      if (e?.response?.status === 401) {
        setToken('')
        localStorage.removeItem('cascadeiq_token')
      }
    },
  })

  const pending = alerts.filter(a => a.status === 'PENDING_VERIFICATION')
  const completed = alerts.filter(a => a.status !== 'PENDING_VERIFICATION')

  if (!token) {
    return (
      <div style={{
        height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--bg-base)',
      }}>
        <div style={{
          padding: '32px', borderRadius: 'var(--radius-xl)',
          background: 'var(--bg-surface)', border: '1px solid var(--border)',
          width: '340px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
            <ShieldCheck size={24} color="var(--teal)" />
            <div>
              <div style={{ fontWeight: 700, fontSize: '16px' }}>Authority Login</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Verification queue access</div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Username</label>
              <input
                id="authority-username"
                type="text"
                value={loginUser}
                onChange={e => setLoginUser(e.target.value)}
                placeholder="authority"
                style={{
                  width: '100%', padding: '8px 12px', borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                  color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', fontSize: '13px',
                }}
              />
            </div>
            <div>
              <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Password</label>
              <input
                id="authority-password"
                type="password"
                value={loginPass}
                onChange={e => setLoginPass(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && loginMutation.mutate()}
                placeholder="••••••••"
                style={{
                  width: '100%', padding: '8px 12px', borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                  color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', fontSize: '13px',
                }}
              />
            </div>
            {loginError && (
              <div style={{ fontSize: '11px', color: 'var(--red)', padding: '8px', background: 'var(--red-dim)', borderRadius: 'var(--radius-md)' }}>
                {loginError}
              </div>
            )}
            <button
              id="login-submit"
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center', marginTop: '4px' }}
              onClick={() => loginMutation.mutate()}
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? 'Authenticating…' : 'Login'}
            </button>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', textAlign: 'center' }}>
              Use the authority credentials configured for this deployment.
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: '20px' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '4px' }}>
              Authority Verification Queue
            </h1>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Human-in-the-loop: no alert reaches public status without verification
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {pending.length > 0 && (
              <div style={{
                padding: '6px 14px', borderRadius: '100px',
                background: 'var(--red-dim)', border: '1px solid rgba(239,68,68,0.3)',
                color: 'var(--red)', fontSize: '12px', fontWeight: 600,
              }}>
                {pending.length} Pending
              </div>
            )}
            <button className="btn btn-ghost" onClick={() => { setToken(''); localStorage.removeItem('cascadeiq_token') }}>
              Logout
            </button>
          </div>
        </div>

        {isLoading && <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}><div className="spinner" /></div>}

        {/* Pending alerts */}
        {pending.length > 0 && (
          <div style={{ marginBottom: '24px' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              ⏳ Awaiting Verification
            </div>
            {pending.map(alert => (
              <AlertCard
                key={alert.id}
                alert={alert}
                note={notes[alert.id] || ''}
                onNoteChange={(n) => setNotes(prev => ({ ...prev, [alert.id]: n }))}
                onVerify={() => verifyMutation.mutate({ id: alert.id, action: 'verify', note: notes[alert.id] })}
                onDismiss={() => verifyMutation.mutate({ id: alert.id, action: 'dismiss', note: notes[alert.id] })}
                isPending={verifyMutation.isPending}
              />
            ))}
          </div>
        )}

        {pending.length === 0 && !isLoading && (
          <div style={{
            padding: '32px', borderRadius: 'var(--radius-lg)', textAlign: 'center',
            background: 'var(--bg-surface)', border: '1px solid var(--border)', marginBottom: '24px',
          }}>
            <CheckCircle2 size={32} color="var(--green)" style={{ margin: '0 auto 12px' }} />
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--green)' }}>Queue Clear</div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>No alerts pending verification</div>
          </div>
        )}

        {/* Completed */}
        {completed.length > 0 && (
          <div>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              ✓ Completed
            </div>
            {completed.slice(0, 10).map(alert => (
              <AlertCard key={alert.id} alert={alert} readonly />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function AlertCard({
  alert, note, onNoteChange, onVerify, onDismiss, isPending, readonly,
}: {
  alert: Alert
  note?: string
  onNoteChange?: (n: string) => void
  onVerify?: () => void
  onDismiss?: () => void
  isPending?: boolean
  readonly?: boolean
}) {
  const TIER_COLORS: Record<string, string> = {
    GREEN: '#22c55e', YELLOW: '#eab308', ORANGE: '#f97316', RED: '#ef4444',
  }
  const tcolor = TIER_COLORS[alert.tier]
  const statusIcon = alert.status === 'VERIFIED' ? <CheckCircle2 size={12} color="var(--green)" />
    : alert.status === 'DISMISSED' ? <XCircle size={12} color="var(--text-muted)" />
    : <Clock size={12} color="var(--yellow)" />

  return (
    <div className="alert-queue-item slide-in-right" style={{ marginBottom: '10px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <TierBadge tier={alert.tier as any} probability={0} />
          <div>
            <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              Alert #{alert.id} · Prediction #{alert.prediction_id}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
              {new Date(alert.created_at).toLocaleString('en-IN')}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: 'var(--text-muted)' }}>
          {statusIcon} {alert.status.replace(/_/g, ' ')}
        </div>
      </div>

      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.6', padding: '8px 10px', background: 'var(--bg-base)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
        {alert.recommended_action}
      </div>

      {alert.verified_by && (
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {alert.status} by <strong>{alert.verified_by}</strong> · {new Date(alert.verified_at!).toLocaleString('en-IN')}
          {alert.notes && ` · "${alert.notes}"`}
        </div>
      )}

      {!readonly && (
        <>
          <textarea
            placeholder="Optional notes for this verification decision…"
            value={note}
            onChange={e => onNoteChange?.(e.target.value)}
            style={{
              width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-elevated)', border: '1px solid var(--border)',
              color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', fontSize: '12px',
              resize: 'vertical', minHeight: '52px',
            }}
          />
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              id={`verify-alert-${alert.id}`}
              className="btn btn-primary"
              onClick={onVerify}
              disabled={isPending}
              style={{ flex: 1, justifyContent: 'center' }}
              aria-label={`Verify alert ${alert.id}`}
            >
              <ShieldCheck size={14} /> Verify &amp; Issue
            </button>
            <button
              id={`dismiss-alert-${alert.id}`}
              className="btn btn-danger"
              onClick={onDismiss}
              disabled={isPending}
              aria-label={`Dismiss alert ${alert.id}`}
            >
              <ShieldX size={14} /> Dismiss
            </button>
          </div>
        </>
      )}
    </div>
  )
}

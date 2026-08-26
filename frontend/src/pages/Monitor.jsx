import { useState, useEffect, useRef } from 'react'
import { monitor } from '../services/api'

export default function Monitor() {
  const [status, setStatus] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [activity, setActivity] = useState([])
  const [pending, setPending] = useState([])
  const [polling, setPolling] = useState(false)
  const [tab, setTab] = useState('alerts')
  const [cfLoggedIn, setCfLoggedIn] = useState(false)
  const [cfEmail, setCfEmail] = useState('')
  const [cfPass, setCfPass] = useState('')
  const [cfLogging, setCfLogging] = useState(false)
  const [cfMsg, setCfMsg] = useState('')
  const intervalRef = useRef(null)

  useEffect(() => {
    loadAll()
    checkCfSession()
    intervalRef.current = setInterval(loadAll, 15000)
    return () => clearInterval(intervalRef.current)
  }, [])

  const checkCfSession = async () => {
    try {
      const res = await monitor.cfSession()
      setCfLoggedIn(res.data.logged_in)
    } catch {}
  }

  const handleCfLogin = async (e) => {
    e.preventDefault()
    setCfLogging(true)
    setCfMsg('')
    try {
      const res = await monitor.cfLogin(cfEmail, cfPass)
      if (res.data.status === 'logged_in') {
        setCfLoggedIn(true)
        setCfMsg('Session active')
        setCfPass('')
      } else {
        setCfMsg('Login failed — check credentials')
      }
    } catch {
      setCfMsg('Login failed')
    } finally {
      setCfLogging(false)
    }
  }

  const loadAll = async () => {
    try {
      const [statusRes, alertsRes, activityRes, pendingRes] = await Promise.all([
        monitor.status(),
        monitor.alerts(),
        monitor.activity(),
        monitor.pending(),
      ])
      setStatus(statusRes.data)
      setAlerts(alertsRes.data)
      setActivity(activityRes.data)
      setPending(pendingRes.data)
    } catch (err) {
      console.error(err)
    }
  }

  const handleToggle = async () => {
    if (status?.running) {
      await monitor.stop()
    } else {
      await monitor.start()
    }
    loadAll()
  }

  const handlePollNow = async () => {
    setPolling(true)
    try {
      await monitor.pollNow()
      await loadAll()
    } finally {
      setPolling(false)
    }
  }

  const tabStyle = (key) => ({
    fontSize: '14px',
    letterSpacing: '0.2em',
    textTransform: 'uppercase',
    padding: '8px 16px',
    border: `1px solid ${tab === key ? '#2a2a2a' : '#1a1a1a'}`,
    background: tab === key ? '#0a0a0a' : 'transparent',
    color: tab === key ? '#e8e4df' : '#6b6560',
    cursor: 'pointer',
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-10">
        <div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '3rem', fontWeight: 300, color: '#e8e4df', letterSpacing: '0.04em' }}>
            Live Monitor
          </h1>
          <p style={{ fontSize: '14px', letterSpacing: '0.15em', color: '#6b6560', marginTop: '8px', textTransform: 'uppercase' }}>
            Auto-detects new submissions and analyzes them
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handlePollNow}
            disabled={polling}
            style={{ fontSize: '14px', letterSpacing: '0.2em', textTransform: 'uppercase', color: '#6b6560', border: '1px solid #1a1a1a', padding: '10px 16px', background: 'transparent', cursor: 'pointer', opacity: polling ? 0.5 : 1 }}
          >
            {polling ? 'POLLING...' : 'POLL NOW'}
          </button>
          <button
            onClick={handleToggle}
            style={{
              fontSize: '14px',
              letterSpacing: '0.2em',
              textTransform: 'uppercase',
              padding: '10px 16px',
              border: `1px solid ${status?.running ? '#2a1515' : '#152a15'}`,
              color: status?.running ? '#c47070' : '#7a9e7a',
              background: 'transparent',
              cursor: 'pointer',
            }}
          >
            {status?.running ? 'STOP MONITOR' : 'START MONITOR'}
          </button>
        </div>
      </div>

      {status && (
        <div style={{ border: '1px solid #1a1a1a', padding: '16px 20px', background: '#0a0a0a', marginBottom: '24px' }}>
          <div className="flex items-center gap-6 flex-wrap">
            <div className="flex items-center gap-2">
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: status.running ? '#7a9e7a' : '#3a3a3a' }} />
              <span style={{ fontSize: '14px', color: status.running ? '#7a9e7a' : '#6b6560', letterSpacing: '0.15em', textTransform: 'uppercase' }}>
                {status.running ? 'Active' : 'Stopped'}
              </span>
            </div>
            {[
              { label: 'Polls', value: status.total_polls },
              { label: 'New subs', value: status.new_submissions },
              { label: 'Source fetched', value: status.source_fetched },
              { label: 'Auto-analyzed', value: status.auto_analyzed },
            ].map((s, i) => (
              <span key={i} style={{ fontSize: '14px', color: '#3a3a3a', letterSpacing: '0.1em' }}>
                <span style={{ color: '#6b6560' }}>{s.label}:</span> {s.value}
              </span>
            ))}
            {status.last_poll && (
              <span style={{ fontSize: '14px', color: '#3a3a3a', letterSpacing: '0.1em' }}>
                <span style={{ color: '#6b6560' }}>Last:</span> {new Date(status.last_poll).toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
      )}

      {/* CF Session */}
      <div style={{ border: '1px solid #1a1a1a', padding: '16px 20px', background: '#0a0a0a', marginBottom: '24px' }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: cfLoggedIn ? '#7a9e7a' : '#c4a882' }} />
            <span style={{ fontSize: '13px', letterSpacing: '0.2em', color: cfLoggedIn ? '#7a9e7a' : '#6b6560', textTransform: 'uppercase' }}>
              CF Session: {cfLoggedIn ? 'Active' : 'Not connected'}
            </span>
            {cfLoggedIn && (
              <span style={{ fontSize: '13px', color: '#3a3a3a', letterSpacing: '0.1em' }}>
                — source code fetch enabled
              </span>
            )}
          </div>
          {cfMsg && <span style={{ fontSize: '13px', color: cfLoggedIn ? '#7a9e7a' : '#c47070', letterSpacing: '0.1em' }}>{cfMsg}</span>}
        </div>
        {!cfLoggedIn && (
          <form onSubmit={handleCfLogin} className="flex items-center gap-3" style={{ marginTop: '12px' }}>
            <input
              type="text"
              placeholder="CF handle or email"
              value={cfEmail}
              onChange={e => setCfEmail(e.target.value)}
              style={{ fontSize: '13px', padding: '8px 12px', background: '#050505', border: '1px solid #1a1a1a', color: '#e8e4df', fontFamily: 'var(--font-mono)', width: '220px' }}
            />
            <input
              type="password"
              placeholder="Password"
              value={cfPass}
              onChange={e => setCfPass(e.target.value)}
              style={{ fontSize: '13px', padding: '8px 12px', background: '#050505', border: '1px solid #1a1a1a', color: '#e8e4df', fontFamily: 'var(--font-mono)', width: '180px' }}
            />
            <button
              type="submit"
              disabled={cfLogging || !cfEmail || !cfPass}
              style={{ fontSize: '12px', letterSpacing: '0.2em', textTransform: 'uppercase', padding: '8px 14px', border: '1px solid #152a15', color: '#7a9e7a', background: 'transparent', cursor: 'pointer', opacity: cfLogging ? 0.5 : 1, whiteSpace: 'nowrap' }}
            >
              {cfLogging ? 'CONNECTING...' : 'CONNECT'}
            </button>
          </form>
        )}
      </div>

      <div className="flex gap-1 mb-6">
        {[
          { key: 'alerts', label: 'Alerts', count: alerts.length },
          { key: 'activity', label: 'Activity', count: activity.length },
          { key: 'pending', label: 'Pending', count: pending.length },
        ].map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} style={tabStyle(t.key)}>
            {t.label}
            {t.count > 0 && (
              <span style={{ marginLeft: '8px', fontSize: '13px', color: t.key === 'alerts' ? '#c47070' : '#6b6560' }}>
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {tab === 'alerts' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {alerts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 0', border: '1px solid #1a1a1a', background: '#0a0a0a' }}>
              <p style={{ fontFamily: 'var(--font-serif)', fontSize: '1.3rem', color: '#6b6560', fontWeight: 300 }}>No anomalies detected.</p>
              <p style={{ fontSize: '14px', color: '#3a3a3a', marginTop: '8px', letterSpacing: '0.1em' }}>Submissions scoring above 0.5 will appear here.</p>
            </div>
          ) : (
            alerts.map(alert => (
              <div key={alert.id} style={{ border: '1px solid #1a1515', padding: '14px 20px', background: '#0a0a0a' }}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div style={{
                      width: '36px',
                      height: '36px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '13px',
                      fontFamily: 'var(--font-mono)',
                      border: `1px solid ${alert.anomaly_score > 0.8 ? '#2a1515' : alert.anomaly_score > 0.6 ? '#2a2015' : '#2a2515'}`,
                      color: alert.anomaly_score > 0.8 ? '#c47070' : alert.anomaly_score > 0.6 ? '#c48060' : '#c4a882',
                    }}>
                      {(alert.anomaly_score * 100).toFixed(0)}
                    </div>
                    <div>
                      <p style={{ fontSize: '14px', color: '#e8e4df', fontFamily: 'var(--font-mono)' }}>{alert.student_handle}</p>
                      <p style={{ fontSize: '14px', color: '#3a3a3a', marginTop: '2px' }}>{alert.problem_name}</p>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{
                      fontSize: '13px',
                      letterSpacing: '0.15em',
                      textTransform: 'uppercase',
                      padding: '3px 8px',
                      border: `1px solid ${alert.verdict === 'ANOMALOUS' ? '#2a1515' : '#2a2515'}`,
                      color: alert.verdict === 'ANOMALOUS' ? '#c47070' : alert.verdict === 'SIGNIFICANT_DEVIATION' ? '#c48060' : '#c4a882',
                    }}>
                      {alert.verdict}
                    </span>
                    <p style={{ fontSize: '14px', color: '#3a3a3a', marginTop: '6px', letterSpacing: '0.05em' }}>
                      {new Date(alert.submitted_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {tab === 'activity' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {activity.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 0', border: '1px solid #1a1a1a', background: '#0a0a0a' }}>
              <p style={{ fontFamily: 'var(--font-serif)', fontSize: '1.3rem', color: '#6b6560', fontWeight: 300 }}>No submissions yet.</p>
            </div>
          ) : (
            activity.map(item => (
              <div key={item.submission_id} className="flex items-center justify-between" style={{ border: '1px solid #1a1a1a', padding: '10px 16px', background: '#0a0a0a' }}>
                <div className="flex items-center gap-3">
                  <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: item.has_source ? '#7a9e7a' : '#c4a882' }} />
                  <div>
                    <span style={{ fontSize: '13px', color: '#e8e4df', fontFamily: 'var(--font-mono)' }}>{item.student_handle}</span>
                    <span style={{ color: '#2a2a2a', margin: '0 8px' }}>&middot;</span>
                    <span style={{ fontSize: '13px', color: '#6b6560' }}>{item.problem_name}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {item.anomaly_score !== null && (
                    <span style={{
                      fontSize: '14px',
                      fontFamily: 'var(--font-mono)',
                      padding: '2px 8px',
                      border: `1px solid ${item.anomaly_score > 0.6 ? '#2a1515' : item.anomaly_score > 0.3 ? '#2a2515' : '#152a15'}`,
                      color: item.anomaly_score > 0.6 ? '#c47070' : item.anomaly_score > 0.3 ? '#c4a882' : '#7a9e7a',
                    }}>
                      {(item.anomaly_score * 100).toFixed(0)}%
                    </span>
                  )}
                  <span style={{ fontSize: '14px', color: '#3a3a3a', letterSpacing: '0.05em' }}>
                    {new Date(item.submitted_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {tab === 'pending' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {pending.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 0', border: '1px solid #1a1a1a', background: '#0a0a0a' }}>
              <p style={{ fontFamily: 'var(--font-serif)', fontSize: '1.3rem', color: '#6b6560', fontWeight: 300 }}>No pending submissions.</p>
              <p style={{ fontSize: '14px', color: '#3a3a3a', marginTop: '8px', letterSpacing: '0.1em' }}>All source code has been collected.</p>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between" style={{ marginBottom: '12px' }}>
                <p style={{ fontSize: '14px', color: '#3a3a3a', letterSpacing: '0.05em', lineHeight: '1.6' }}>
                  {pending.length} submissions detected but source code not yet fetched.{!cfLoggedIn && ' Set CF cookies above to enable fetching.'}
                </p>
                {cfLoggedIn && (
                  <button
                    onClick={async () => {
                      try {
                        const res = await monitor.fetchPending()
                        setCfMsg(`Fetched ${res.data.fetched} of ${res.data.total_pending}`)
                        loadAll()
                      } catch {}
                    }}
                    style={{ fontSize: '12px', letterSpacing: '0.2em', textTransform: 'uppercase', padding: '8px 14px', border: '1px solid #152a15', color: '#7a9e7a', background: 'transparent', cursor: 'pointer', whiteSpace: 'nowrap' }}
                  >
                    FETCH ALL
                  </button>
                )}
              </div>
              {pending.map(item => (
                <div key={item.id} className="flex items-center justify-between" style={{ border: '1px solid #1a1a18', padding: '10px 16px', background: '#0a0a0a' }}>
                  <div>
                    <span style={{ fontSize: '13px', color: '#e8e4df', fontFamily: 'var(--font-mono)' }}>{item.student_handle}</span>
                    <span style={{ color: '#2a2a2a', margin: '0 8px' }}>&middot;</span>
                    <span style={{ fontSize: '13px', color: '#6b6560' }}>{item.problem_name}</span>
                  </div>
                  <span style={{ fontSize: '14px', color: '#3a3a3a', letterSpacing: '0.05em' }}>
                    {new Date(item.submitted_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  )
}

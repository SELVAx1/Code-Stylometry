import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { analysis, submissions } from '../services/api'
import ScoreBadge from '../components/ScoreBadge'

export default function StudentDetail() {
  const { studentId } = useParams()
  const [results, setResults] = useState([])
  const [subCount, setSubCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [building, setBuilding] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => {
    loadData()
  }, [studentId])

  const loadData = async () => {
    try {
      const [resultsRes, countRes] = await Promise.all([
        analysis.getResults(studentId),
        submissions.getCount(studentId),
      ])
      setResults(resultsRes.data)
      setSubCount(countRes.data.count)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleBuildProfile = async () => {
    setBuilding(true)
    try {
      await analysis.buildProfile(studentId)
      loadData()
    } catch (err) {
      alert(err.response?.data?.detail || 'Error building profile')
    } finally {
      setBuilding(false)
    }
  }

  const handleAnalyzeAll = async () => {
    setAnalyzing(true)
    try {
      const subsRes = await submissions.getByStudent(studentId)
      for (const sub of subsRes.data) {
        try {
          await analysis.analyzeSubmission(sub.id)
        } catch {}
      }
      loadData()
    } catch (err) {
      console.error(err)
    } finally {
      setAnalyzing(false)
    }
  }

  const chartData = results
    .slice()
    .reverse()
    .map((r, i) => ({
      index: i + 1,
      score: r.anomaly_score,
      name: r.problem_name || `#${i + 1}`,
      date: new Date(r.submitted_at || r.created_at).toLocaleDateString(),
    }))

  if (loading) {
    return <div style={{ color: '#6b6560', textAlign: 'center', paddingTop: '80px', fontSize: '13px', letterSpacing: '0.2em' }}>LOADING...</div>
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-2">
        <Link to="/" style={{ fontSize: '13px', letterSpacing: '0.15em', color: '#6b6560', textTransform: 'uppercase' }}>Dashboard</Link>
        <span style={{ color: '#2a2a2a' }}>/</span>
        <span style={{ fontSize: '13px', letterSpacing: '0.15em', color: '#e8e4df', textTransform: 'uppercase' }}>Student Analysis</span>
      </div>

      <div className="flex items-center justify-between mb-10 mt-6">
        <div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '3rem', fontWeight: 300, color: '#e8e4df', letterSpacing: '0.04em' }}>
            Student Analysis
          </h1>
          <p style={{ fontSize: '14px', letterSpacing: '0.15em', color: '#6b6560', marginTop: '8px', textTransform: 'uppercase' }}>
            {subCount} submissions collected
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleBuildProfile}
            disabled={building}
            style={{ fontSize: '14px', letterSpacing: '0.2em', textTransform: 'uppercase', color: '#6b6560', border: '1px solid #1a1a1a', padding: '10px 16px', background: 'transparent', cursor: 'pointer', opacity: building ? 0.5 : 1 }}
          >
            {building ? 'BUILDING...' : 'BUILD PROFILE'}
          </button>
          <button
            onClick={handleAnalyzeAll}
            disabled={analyzing}
            style={{ fontSize: '14px', letterSpacing: '0.2em', textTransform: 'uppercase', color: '#e8e4df', border: '1px solid #2a2a2a', padding: '10px 16px', background: 'transparent', cursor: 'pointer', opacity: analyzing ? 0.5 : 1 }}
          >
            {analyzing ? 'ANALYZING...' : 'ANALYZE RECENT'}
          </button>
        </div>
      </div>

      {chartData.length > 0 && (
        <div style={{ border: '1px solid #1a1a1a', padding: '24px', background: '#0a0a0a', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '13px', letterSpacing: '0.2em', color: '#6b6560', textTransform: 'uppercase', marginBottom: '16px', fontFamily: 'var(--font-mono)', fontWeight: 400 }}>
            Anomaly Score Timeline
          </h2>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
              <XAxis dataKey="index" stroke="#3a3a3a" fontSize={10} fontFamily="Space Mono" />
              <YAxis domain={[0, 1]} stroke="#3a3a3a" fontSize={10} fontFamily="Space Mono" />
              <Tooltip
                contentStyle={{ background: '#0a0a0a', border: '1px solid #1a1a1a', borderRadius: '0', fontFamily: 'Space Mono', fontSize: '13px' }}
                labelStyle={{ color: '#6b6560' }}
                itemStyle={{ color: '#c4a882' }}
              />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#c4a882"
                strokeWidth={1.5}
                dot={{ fill: '#c4a882', r: 2.5 }}
                activeDot={{ r: 4, fill: '#e8e4df' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {results.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', border: '1px solid #1a1a1a', background: '#0a0a0a' }}>
          <p style={{ fontFamily: 'var(--font-serif)', fontSize: '1.3rem', color: '#6b6560', fontWeight: 300 }}>No analysis results yet.</p>
          <p style={{ fontSize: '14px', color: '#3a3a3a', marginTop: '8px', letterSpacing: '0.1em' }}>Build a profile first, then analyze submissions.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {results.map((result) => (
            <Link
              key={result.id}
              to={`/submissions/${result.submission_id}`}
              style={{
                display: 'block',
                border: '1px solid #1a1a1a',
                padding: '14px 20px',
                background: '#0a0a0a',
                textDecoration: 'none',
                transition: 'border-color 0.2s',
              }}
              onMouseOver={(e) => e.currentTarget.style.borderColor = '#2a2a2a'}
              onMouseOut={(e) => e.currentTarget.style.borderColor = '#1a1a1a'}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <ScoreBadge score={result.anomaly_score} />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                    <span style={{ fontSize: '14px', color: '#e8e4df', fontFamily: 'var(--font-mono)' }}>
                      {result.problem_name || 'Unknown Problem'}
                    </span>
                    <span style={{ fontSize: '14px', color: '#3a3a3a', letterSpacing: '0.1em' }}>
                      {new Date(result.submitted_at || result.created_at).toLocaleDateString('en-US', {
                        year: 'numeric', month: 'short', day: 'numeric'
                      })}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {result.ai_score > 0.5 && (
                    <span style={{ fontSize: '13px', letterSpacing: '0.1em', color: '#9070c4', border: '1px solid #2a2040', padding: '3px 8px' }}>
                      AI: {(result.ai_score * 100).toFixed(0)}%
                    </span>
                  )}
                  <span style={{
                    fontSize: '13px',
                    letterSpacing: '0.15em',
                    textTransform: 'uppercase',
                    color: result.verdict === 'AUTHENTIC' ? '#7a9e7a' :
                      result.verdict === 'ANOMALOUS' ? '#c47070' : '#c4a882'
                  }}>
                    {result.verdict}
                  </span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3a3a3a" strokeWidth="1.5">
                    <path d="M9 18l6-6-6-6" />
                  </svg>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

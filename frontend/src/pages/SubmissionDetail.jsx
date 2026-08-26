import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { submissions } from '../services/api'
import ScoreBadge from '../components/ScoreBadge'

const FEATURE_LABELS = {
  avg_line_length: 'Average line length',
  blank_line_ratio: 'Blank line usage',
  code_density: 'Code density',
  indent_consistency: 'Indentation consistency',
  brace_same_line_ratio: 'Brace placement style',
  camel_case_ratio: 'camelCase naming',
  lines_per_function: 'Function length',
  unique_token_ratio: 'Vocabulary diversity',
  uses_cin: 'Uses cin/cout vs scanf/printf',
  uses_bits_stdc: 'Uses bits/stdc++.h',
  punct_comma_ratio: 'Comma usage',
  punct_open_brace_ratio: 'Brace frequency',
  punct_angle_bracket_ratio: 'Template/angle bracket usage',
  kw_freq_long: 'Long keyword frequency',
  kw_freq_return: 'Return statement frequency',
  increment_style_postfix: 'Uses i++ vs ++i',
  avg_identifier_length: 'Variable name length',
  max_nesting_depth: 'Nesting depth',
  comment_ratio: 'Comment density',
}

function getFeatureLabel(key) {
  return FEATURE_LABELS[key] || key.replace(/_/g, ' ')
}

function getExplanation(analysis) {
  const score = analysis.anomaly_score
  const deviations = analysis.feature_deviations || {}
  const crossMatches = analysis.cross_matches || []

  const topDevs = Object.entries(deviations)
    .sort((a, b) => b[1].z_score - a[1].z_score)
    .slice(0, 8)

  const highCount = Object.values(deviations).filter(d => d.severity === 'HIGH').length
  const medCount = Object.values(deviations).filter(d => d.severity === 'MEDIUM').length
  const lowCount = Object.values(deviations).filter(d => d.severity === 'LOW').length

  let summary = ''
  if (score < 0.3) {
    summary = 'This submission matches the student\'s usual coding style. No significant deviations detected across the analyzed features.'
  } else if (score < 0.6) {
    summary = `This submission has some differences from the student's typical style. ${highCount} feature(s) deviate significantly, which may indicate experimentation or learning new patterns.`
  } else if (score < 0.8) {
    summary = `This submission shows significant deviation from the student's established coding patterns. ${highCount} features are highly unusual for this student — possible external assistance or collaboration.`
  } else {
    summary = `This submission is highly anomalous — it does NOT match this student's coding style. ${highCount} features are drastically different from their norm. This strongly suggests the code was not written by this student.`
  }

  return { summary, topDevs, highCount, medCount, lowCount, crossMatches }
}

export default function SubmissionDetail() {
  const { submissionId } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadData()
  }, [submissionId])

  const loadData = async () => {
    try {
      const res = await submissions.getDetail(submissionId)
      setData(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load submission')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div style={{ color: '#6b6560', textAlign: 'center', paddingTop: '80px', fontSize: '13px', letterSpacing: '0.2em' }}>LOADING...</div>
  }

  if (error) {
    return <div style={{ color: '#c47070', textAlign: 'center', paddingTop: '80px', fontSize: '13px', letterSpacing: '0.15em' }}>{error}</div>
  }

  const analysis = data.analysis
  const explanation = analysis ? getExplanation(analysis) : null

  return (
    <div>
      <div className="flex items-center gap-3 mb-2">
        <Link to="/" style={{ fontSize: '13px', letterSpacing: '0.15em', color: '#6b6560', textTransform: 'uppercase' }}>Dashboard</Link>
        <span style={{ color: '#2a2a2a' }}>/</span>
        <Link to={`/students/${data.student_id}`} style={{ fontSize: '13px', letterSpacing: '0.15em', color: '#6b6560', textTransform: 'uppercase' }}>{data.student_name || data.student_handle}</Link>
        <span style={{ color: '#2a2a2a' }}>/</span>
        <span style={{ fontSize: '13px', letterSpacing: '0.15em', color: '#e8e4df', textTransform: 'uppercase' }}>Submission</span>
      </div>

      <div className="flex items-center justify-between mb-8 mt-6">
        <div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '2.4rem', fontWeight: 300, color: '#e8e4df', letterSpacing: '0.04em' }}>
            {data.problem_name || 'Unknown Problem'}
          </h1>
          <div className="flex items-center gap-4" style={{ marginTop: '10px' }}>
            <span style={{ fontSize: '14px', letterSpacing: '0.15em', color: '#6b6560', textTransform: 'uppercase' }}>
              {data.student_name} ({data.student_handle})
            </span>
            <span style={{ color: '#2a2a2a' }}>|</span>
            <span style={{ fontSize: '14px', letterSpacing: '0.1em', color: '#6b6560' }}>
              {new Date(data.submitted_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </span>
            <span style={{ color: '#2a2a2a' }}>|</span>
            <span style={{ fontSize: '14px', letterSpacing: '0.1em', color: '#6b6560' }}>
              {data.language}
            </span>
            <span style={{ color: '#2a2a2a' }}>|</span>
            <span style={{ fontSize: '14px', letterSpacing: '0.1em', color: data.verdict === 'OK' ? '#7a9e7a' : '#c4a882' }}>
              {data.verdict}
            </span>
          </div>
        </div>
        {analysis && <ScoreBadge score={analysis.anomaly_score} size="lg" />}
      </div>

      {/* Source Code */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <h2 style={{ fontSize: '13px', letterSpacing: '0.2em', color: '#6b6560', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 400 }}>
            Source Code
          </h2>
          <span style={{ fontSize: '13px', letterSpacing: '0.1em', color: '#3a3a3a' }}>
            CF #{data.cf_submission_id}
          </span>
        </div>
        <div style={{ border: '1px solid #1a1a1a', background: '#050505', overflow: 'auto', maxHeight: '500px' }}>
          <pre style={{
            margin: 0,
            padding: '20px',
            fontSize: '14px',
            lineHeight: '1.7',
            fontFamily: 'var(--font-mono)',
            color: '#b0aca6',
            whiteSpace: 'pre',
            tabSize: 4,
          }}>
            {data.source_code || 'Source code not available.'}
          </pre>
        </div>
      </div>

      {/* Analysis Section */}
      {!analysis ? (
        <div style={{ textAlign: 'center', padding: '40px 0', border: '1px solid #1a1a1a', background: '#0a0a0a' }}>
          <p style={{ fontFamily: 'var(--font-serif)', fontSize: '1.2rem', color: '#6b6560', fontWeight: 300 }}>No analysis available.</p>
          <p style={{ fontSize: '14px', color: '#3a3a3a', marginTop: '8px', letterSpacing: '0.1em' }}>Build a profile and analyze this submission first.</p>
        </div>
      ) : (
        <div>
          <h2 style={{ fontSize: '13px', letterSpacing: '0.2em', color: '#6b6560', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 400, marginBottom: '16px' }}>
            Analysis
          </h2>

          {/* Verdict Summary */}
          <div style={{
            padding: '18px 20px',
            fontSize: '14px',
            lineHeight: '1.7',
            letterSpacing: '0.02em',
            color: analysis.anomaly_score > 0.6 ? '#c47070' :
              analysis.anomaly_score > 0.3 ? '#c4a882' : '#7a9e7a',
            border: `1px solid ${analysis.anomaly_score > 0.6 ? '#2a1515' :
              analysis.anomaly_score > 0.3 ? '#2a2515' : '#152a15'}`,
            background: analysis.anomaly_score > 0.6 ? '#0f0808' :
              analysis.anomaly_score > 0.3 ? '#0f0d08' : '#080f08',
            marginBottom: '20px',
          }}>
            {explanation.summary}
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-5 gap-3" style={{ marginBottom: '24px' }}>
            {[
              { value: `${(analysis.anomaly_score * 100).toFixed(0)}%`, label: 'Anomaly Score' },
              { value: analysis.verdict, label: 'Verdict' },
              { value: explanation.highCount, label: 'High Deviations' },
              { value: explanation.medCount, label: 'Medium Deviations' },
              { value: explanation.crossMatches.length, label: 'Cross Matches' },
            ].map((stat, i) => (
              <div key={i} style={{ background: '#080808', border: '1px solid #141414', padding: '14px', textAlign: 'center' }}>
                <div style={{ fontFamily: 'var(--font-serif)', fontSize: '1.3rem', fontWeight: 300, color: '#e8e4df' }}>{stat.value}</div>
                <div style={{ fontSize: '10px', letterSpacing: '0.15em', color: '#3a3a3a', textTransform: 'uppercase', marginTop: '6px' }}>{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Cross Matches */}
          {explanation.crossMatches.length > 0 && (
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '13px', letterSpacing: '0.2em', color: '#6b6560', textTransform: 'uppercase', marginBottom: '12px', fontFamily: 'var(--font-mono)', fontWeight: 400 }}>
                Same Problem — Code Similarity With Other Students
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {explanation.crossMatches.map((match, i) => (
                  <div key={i} className="flex items-center justify-between" style={{ background: '#080808', border: '1px solid #141414', padding: '12px 16px' }}>
                    <span style={{ fontSize: '13px', color: '#e8e4df', fontFamily: 'var(--font-mono)' }}>
                      {match.student_name || match.handle || match.student_id || `Student ${i + 1}`}
                    </span>
                    <div className="flex items-center gap-3">
                      <div style={{ width: '100px', height: '3px', background: '#1a1a1a', overflow: 'hidden' }}>
                        <div style={{ height: '100%', background: '#c48060', width: `${(match.similarity || 0) * 100}%` }} />
                      </div>
                      <span style={{ fontSize: '14px', color: '#c48060', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em', minWidth: '80px', textAlign: 'right' }}>
                        {((match.similarity || 0) * 100).toFixed(0)}% similar
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Feature Deviations */}
          <div>
            <h3 style={{ fontSize: '13px', letterSpacing: '0.2em', color: '#6b6560', textTransform: 'uppercase', marginBottom: '12px', fontFamily: 'var(--font-mono)', fontWeight: 400 }}>
              Style Differences vs Their Usual Code
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {explanation.topDevs.map(([feature, deviation]) => (
                <div key={feature} style={{ background: '#080808', border: '1px solid #141414', padding: '12px 16px' }}>
                  <div className="flex items-center justify-between" style={{ marginBottom: '8px' }}>
                    <span style={{ fontSize: '13px', color: '#e8e4df', fontFamily: 'var(--font-mono)' }}>{getFeatureLabel(feature)}</span>
                    <span style={{
                      fontSize: '13px',
                      letterSpacing: '0.1em',
                      padding: '3px 10px',
                      border: `1px solid ${deviation.severity === 'HIGH' ? '#2a1515' : deviation.severity === 'MEDIUM' ? '#2a2515' : '#152a15'}`,
                      color: deviation.severity === 'HIGH' ? '#c47070' : deviation.severity === 'MEDIUM' ? '#c4a882' : '#7a9e7a',
                    }}>
                      {deviation.z_score.toFixed(1)}x deviation
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '3px', background: '#1a1a1a', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: `${Math.min(100, (deviation.z_score / 8) * 100)}%`,
                      background: deviation.severity === 'HIGH' ? '#c47070' : deviation.severity === 'MEDIUM' ? '#c4a882' : '#7a9e7a',
                    }} />
                  </div>
                  <div className="flex justify-between" style={{ marginTop: '6px' }}>
                    <span style={{ fontSize: '13px', color: '#3a3a3a', letterSpacing: '0.05em' }}>
                      Expected: {deviation.expected !== undefined ? deviation.expected.toFixed(3) : '—'}
                    </span>
                    <span style={{ fontSize: '13px', color: '#6b6560', letterSpacing: '0.05em' }}>
                      Actual: {deviation.actual !== undefined ? deviation.actual.toFixed(3) : '—'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

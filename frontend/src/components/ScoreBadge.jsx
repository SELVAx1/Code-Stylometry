export default function ScoreBadge({ score, size = 'md' }) {
  const getStyle = () => {
    if (score < 0.3) return { color: '#7a9e7a', borderColor: '#2a3a2a' }
    if (score < 0.6) return { color: '#c4a882', borderColor: '#3a3020' }
    if (score < 0.8) return { color: '#c48060', borderColor: '#3a2820' }
    return { color: '#c47070', borderColor: '#3a2020' }
  }

  const getLabel = () => {
    if (score < 0.3) return 'Authentic'
    if (score < 0.6) return 'Minor'
    if (score < 0.8) return 'Significant'
    return 'Anomalous'
  }

  const s = getStyle()
  const isLg = size === 'lg'

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
      border: `1px solid ${s.borderColor}`,
      padding: isLg ? '8px 16px' : '4px 10px',
      color: s.color,
      fontSize: isLg ? '16px' : '12px',
      letterSpacing: '0.1em',
      fontFamily: 'var(--font-mono)',
    }}>
      <span>{(score * 100).toFixed(0)}%</span>
      <span style={{ textTransform: 'uppercase', letterSpacing: '0.15em' }}>{getLabel()}</span>
    </span>
  )
}

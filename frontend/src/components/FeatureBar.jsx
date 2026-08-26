export default function FeatureBar({ feature, deviation }) {
  const width = Math.min(100, (deviation.z_score / 10) * 100)

  const getColor = () => {
    if (deviation.severity === 'LOW') return '#7a9e7a'
    if (deviation.severity === 'MEDIUM') return '#c4a882'
    return '#c47070'
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '6px 0' }}>
      <span style={{ fontSize: '12px', color: '#6b6560', width: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' }}>
        {feature}
      </span>
      <div style={{ flex: 1, height: '3px', background: '#1a1a1a', overflow: 'hidden' }}>
        <div style={{ height: '100%', background: getColor(), width: `${width}%` }} />
      </div>
      <span style={{ fontSize: '12px', color: '#6b6560', width: '40px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
        {deviation.z_score}
      </span>
      <span style={{ fontSize: '11px', width: '55px', textAlign: 'right', letterSpacing: '0.1em', textTransform: 'uppercase', color: getColor() }}>
        {deviation.severity}
      </span>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { groups, submissions, analysis } from '../services/api'
import ScoreBadge from '../components/ScoreBadge'

export default function GroupDetail() {
  const { groupId } = useParams()
  const [group, setGroup] = useState(null)
  const [students, setStudents] = useState([])
  const [summary, setSummary] = useState([])
  const [showAdd, setShowAdd] = useState(false)
  const [cfHandle, setCfHandle] = useState('')
  const [studentName, setStudentName] = useState('')
  const [collecting, setCollecting] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [groupId])

  const loadData = async () => {
    try {
      const [groupRes, studentsRes] = await Promise.all([
        groups.get(groupId),
        groups.listStudents(groupId),
      ])
      setGroup(groupRes.data)
      setStudents(studentsRes.data)
      try {
        const summaryRes = await analysis.getGroupSummary(groupId)
        setSummary(summaryRes.data)
      } catch {}
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddStudent = async (e) => {
    e.preventDefault()
    if (!cfHandle.trim() || !studentName.trim()) return
    try {
      await groups.addStudent(groupId, { cf_handle: cfHandle, name: studentName })
      setCfHandle('')
      setStudentName('')
      setShowAdd(false)
      loadData()
    } catch (err) {
      console.error(err)
    }
  }

  const handleCollectAll = async () => {
    setCollecting(true)
    try {
      await submissions.collectGroup(groupId, 200)
      loadData()
    } catch (err) {
      console.error(err)
    } finally {
      setCollecting(false)
    }
  }

  const getSummaryForStudent = (studentId) => summary.find((s) => s.student_id === studentId)

  if (loading) {
    return <div style={{ color: '#6b6560', textAlign: 'center', paddingTop: '80px', fontSize: '13px', letterSpacing: '0.2em' }}>LOADING...</div>
  }

  const inputStyle = {
    flex: 1,
    padding: '12px 16px',
    background: '#0a0a0a',
    border: '1px solid #1a1a1a',
    color: '#e8e4df',
    fontSize: '13px',
    letterSpacing: '0.15em',
    fontFamily: 'var(--font-mono)',
    outline: 'none',
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-2">
        <Link to="/" style={{ fontSize: '13px', letterSpacing: '0.15em', color: '#6b6560', textTransform: 'uppercase' }}>Dashboard</Link>
        <span style={{ color: '#2a2a2a' }}>/</span>
        <span style={{ fontSize: '13px', letterSpacing: '0.15em', color: '#e8e4df', textTransform: 'uppercase' }}>{group?.name}</span>
      </div>

      <div className="flex items-center justify-between mb-10 mt-6">
        <div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '3rem', fontWeight: 300, color: '#e8e4df', letterSpacing: '0.04em' }}>
            {group?.name}
          </h1>
          <p style={{ fontSize: '14px', letterSpacing: '0.15em', color: '#6b6560', marginTop: '8px', textTransform: 'uppercase' }}>
            {students.length} students | Code: {group?.code}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleCollectAll}
            disabled={collecting}
            style={{ fontSize: '14px', letterSpacing: '0.2em', textTransform: 'uppercase', color: '#6b6560', border: '1px solid #1a1a1a', padding: '10px 16px', background: 'transparent', cursor: 'pointer', opacity: collecting ? 0.5 : 1 }}
          >
            {collecting ? 'COLLECTING...' : 'FETCH ALL'}
          </button>
          <button
            onClick={() => setShowAdd(true)}
            style={{ fontSize: '14px', letterSpacing: '0.2em', textTransform: 'uppercase', color: '#e8e4df', border: '1px solid #2a2a2a', padding: '10px 16px', background: 'transparent', cursor: 'pointer' }}
          >
            + ADD STUDENT
          </button>
        </div>
      </div>

      {showAdd && (
        <form onSubmit={handleAddStudent} className="mb-8 flex gap-3" style={{ borderBottom: '1px solid #1a1a1a', paddingBottom: '24px' }}>
          <input type="text" value={studentName} onChange={(e) => setStudentName(e.target.value)} placeholder="STUDENT NAME" style={inputStyle} autoFocus />
          <input type="text" value={cfHandle} onChange={(e) => setCfHandle(e.target.value)} placeholder="CF HANDLE" style={inputStyle} />
          <button type="submit" style={{ padding: '12px 20px', background: '#e8e4df', color: '#000', fontSize: '14px', letterSpacing: '0.2em', fontFamily: 'var(--font-mono)', fontWeight: 700, border: 'none', cursor: 'pointer' }}>ADD</button>
          <button type="button" onClick={() => setShowAdd(false)} style={{ padding: '12px 20px', background: 'transparent', color: '#6b6560', fontSize: '14px', letterSpacing: '0.2em', border: '1px solid #1a1a1a', cursor: 'pointer' }}>CANCEL</button>
        </form>
      )}

      {students.length === 0 ? (
        <div className="text-center" style={{ padding: '80px 0' }}>
          <p style={{ fontFamily: 'var(--font-serif)', fontSize: '1.5rem', color: '#6b6560', fontWeight: 300 }}>No students yet.</p>
        </div>
      ) : (
        <div style={{ border: '1px solid #1a1a1a' }}>
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: '1px solid #1a1a1a' }}>
                <th style={{ textAlign: 'left', padding: '14px 20px', fontSize: '13px', letterSpacing: '0.2em', color: '#6b6560', textTransform: 'uppercase', fontWeight: 400 }}>Student</th>
                <th style={{ textAlign: 'left', padding: '14px 20px', fontSize: '13px', letterSpacing: '0.2em', color: '#6b6560', textTransform: 'uppercase', fontWeight: 400 }}>Handle</th>
                <th style={{ textAlign: 'left', padding: '14px 20px', fontSize: '13px', letterSpacing: '0.2em', color: '#6b6560', textTransform: 'uppercase', fontWeight: 400 }}>Analyzed</th>
                <th style={{ textAlign: 'left', padding: '14px 20px', fontSize: '13px', letterSpacing: '0.2em', color: '#6b6560', textTransform: 'uppercase', fontWeight: 400 }}>Anomalies</th>
                <th style={{ textAlign: 'left', padding: '14px 20px', fontSize: '13px', letterSpacing: '0.2em', color: '#6b6560', textTransform: 'uppercase', fontWeight: 400 }}>Score</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => {
                const s = getSummaryForStudent(student.id)
                return (
                  <tr key={student.id} style={{ borderBottom: '1px solid #0f0f0f' }} className="hover:bg-[#0a0a0a] transition">
                    <td style={{ padding: '14px 20px' }}>
                      <Link to={`/students/${student.id}`} style={{ color: '#e8e4df', fontFamily: 'var(--font-serif)', fontSize: '1.1rem', fontWeight: 400, letterSpacing: '0.02em' }}>
                        {student.name}
                      </Link>
                    </td>
                    <td style={{ padding: '14px 20px', fontSize: '13px', color: '#6b6560', fontFamily: 'var(--font-mono)' }}>{student.cf_handle}</td>
                    <td style={{ padding: '14px 20px', fontSize: '13px', color: '#6b6560' }}>{s?.total_analyzed || 0}</td>
                    <td style={{ padding: '14px 20px' }}>
                      {s?.anomaly_count > 0 ? (
                        <span style={{ color: '#c47070', fontSize: '13px', letterSpacing: '0.1em' }}>{s.anomaly_count} flagged</span>
                      ) : (
                        <span style={{ color: '#3a3a3a', fontSize: '13px' }}>--</span>
                      )}
                    </td>
                    <td style={{ padding: '14px 20px' }}>
                      {s ? <ScoreBadge score={s.avg_anomaly_score} /> : <span style={{ color: '#3a3a3a', fontSize: '13px' }}>--</span>}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

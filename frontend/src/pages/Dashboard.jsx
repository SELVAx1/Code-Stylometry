import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { groups } from '../services/api'

export default function Dashboard() {
  const [groupList, setGroupList] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadGroups()
  }, [])

  const loadGroups = async () => {
    try {
      const res = await groups.list()
      setGroupList(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!newGroupName.trim()) return
    try {
      await groups.create(newGroupName)
      setNewGroupName('')
      setShowCreate(false)
      loadGroups()
    } catch (err) {
      console.error(err)
    }
  }

  if (loading) {
    return <div style={{ color: '#6b6560', textAlign: 'center', paddingTop: '80px', fontSize: '13px', letterSpacing: '0.2em' }}>LOADING...</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-12">
        <div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '3rem', fontWeight: 300, color: '#e8e4df', letterSpacing: '0.04em' }}>
            Dashboard
          </h1>
          <p style={{ fontSize: '13px', letterSpacing: '0.15em', color: '#6b6560', marginTop: '8px', textTransform: 'uppercase' }}>
            Manage groups and monitor submissions
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          style={{
            fontSize: '12px',
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
            color: '#e8e4df',
            border: '1px solid #2a2a2a',
            padding: '10px 20px',
            borderRadius: '0',
            background: 'transparent',
            cursor: 'pointer',
            transition: 'border-color 0.2s',
          }}
        >
          + New Group
        </button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} className="mb-8 flex gap-3" style={{ borderBottom: '1px solid #1a1a1a', paddingBottom: '24px' }}>
          <input
            type="text"
            value={newGroupName}
            onChange={(e) => setNewGroupName(e.target.value)}
            placeholder="GROUP NAME"
            style={{
              flex: 1,
              padding: '12px 16px',
              background: '#0a0a0a',
              border: '1px solid #1a1a1a',
              color: '#e8e4df',
              fontSize: '13px',
              letterSpacing: '0.15em',
              fontFamily: 'var(--font-mono)',
              outline: 'none',
            }}
            autoFocus
          />
          <button type="submit" style={{ padding: '12px 20px', background: '#e8e4df', color: '#000', fontSize: '12px', letterSpacing: '0.2em', fontFamily: 'var(--font-mono)', fontWeight: 700, border: 'none', cursor: 'pointer' }}>
            CREATE
          </button>
          <button type="button" onClick={() => setShowCreate(false)} style={{ padding: '12px 20px', background: 'transparent', color: '#6b6560', fontSize: '12px', letterSpacing: '0.2em', border: '1px solid #1a1a1a', cursor: 'pointer' }}>
            CANCEL
          </button>
        </form>
      )}

      {groupList.length === 0 ? (
        <div className="text-center" style={{ padding: '80px 0' }}>
          <p style={{ fontFamily: 'var(--font-serif)', fontSize: '1.5rem', color: '#6b6560', fontWeight: 300 }}>No groups yet.</p>
          <button
            onClick={() => setShowCreate(true)}
            style={{ marginTop: '20px', fontSize: '12px', letterSpacing: '0.2em', color: '#e8e4df', border: '1px solid #2a2a2a', padding: '10px 24px', background: 'transparent', cursor: 'pointer' }}
          >
            CREATE YOUR FIRST GROUP
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {groupList.map((group) => (
            <Link
              key={group.id}
              to={`/groups/${group.id}`}
              className="block transition"
              style={{
                border: '1px solid #1a1a1a',
                padding: '28px',
                background: '#0a0a0a',
              }}
              onMouseOver={(e) => e.currentTarget.style.borderColor = '#3a3a3a'}
              onMouseOut={(e) => e.currentTarget.style.borderColor = '#1a1a1a'}
            >
              <h3 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.8rem', fontWeight: 300, color: '#e8e4df', letterSpacing: '0.03em' }}>
                {group.name}
              </h3>
              <div className="mt-4 flex items-center gap-6" style={{ fontSize: '12px', letterSpacing: '0.15em', color: '#6b6560', textTransform: 'uppercase' }}>
                <span>{group.student_count} students</span>
                <span style={{ color: '#2a2a2a' }}>|</span>
                <span>Code: {group.code}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

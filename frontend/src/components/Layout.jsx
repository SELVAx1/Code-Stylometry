import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  const isActive = (path) => location.pathname === path

  return (
    <div className="min-h-screen" style={{ background: '#000' }}>
      <nav className="border-b" style={{ borderColor: '#1a1a1a' }}>
        <div className="max-w-7xl mx-auto px-8 py-5 flex items-center justify-between">
          <div className="flex items-center gap-10">
            <Link to="/" className="flex items-center gap-3">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-white">
                <path d="M12 2L12 22M2 12L22 12M5.5 5.5L18.5 18.5M18.5 5.5L5.5 18.5" />
              </svg>
              <span style={{ fontFamily: 'var(--font-serif)', fontSize: '1.2rem', fontWeight: 300, letterSpacing: '0.08em', color: '#e8e4df' }}>
                CODE STYLOMETRY
              </span>
            </Link>
            <div className="flex items-center gap-6">
              <Link
                to="/"
                className="transition"
                style={{
                  fontSize: '13px',
                  letterSpacing: '0.15em',
                  textTransform: 'uppercase',
                  color: isActive('/') ? '#e8e4df' : '#6b6560',
                }}
              >
                Groups
              </Link>
              <Link
                to="/monitor"
                className="transition"
                style={{
                  fontSize: '13px',
                  letterSpacing: '0.15em',
                  textTransform: 'uppercase',
                  color: isActive('/monitor') ? '#e8e4df' : '#6b6560',
                }}
              >
                Monitor
              </Link>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="transition hover:opacity-80"
            style={{
              fontSize: '13px',
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              color: '#6b6560',
              border: '1px solid #2a2a2a',
              padding: '6px 16px',
              borderRadius: '20px',
            }}
          >
            Logout
          </button>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-8 py-10">
        <Outlet />
      </main>
    </div>
  )
}

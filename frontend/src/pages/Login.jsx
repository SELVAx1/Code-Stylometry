import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { auth } from '../services/api'

export default function Login() {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isRegister) {
        await auth.register({ email, password, full_name: fullName })
      }
      const res = await auth.login(email, password)
      const token = res.data.access_token
      if (token) {
        localStorage.setItem('token', token)
        window.location.href = '/'
        return
      } else {
        setError('No token received')
      }
    } catch (err) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'string') {
        setError(detail)
      } else {
        setError('Invalid credentials')
      }
    } finally {
      setLoading(false)
    }
  }

  const inputStyle = {
    width: '100%',
    padding: '14px 16px',
    background: '#0a0a0a',
    border: '1px solid #1a1a1a',
    color: '#e8e4df',
    fontSize: '13px',
    letterSpacing: '0.15em',
    fontFamily: 'var(--font-mono)',
    outline: 'none',
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: '#000' }}>
      <div className="w-full max-w-sm">
        <div className="text-center mb-12">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="mx-auto mb-6" style={{ color: '#e8e4df' }}>
            <path d="M12 2L12 22M2 12L22 12M5.5 5.5L18.5 18.5M18.5 5.5L5.5 18.5" />
          </svg>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '2.5rem', fontWeight: 300, letterSpacing: '0.06em', color: '#e8e4df' }}>
            CODE STYLOMETRY
          </h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div style={{ fontSize: '13px', color: '#c47070', textAlign: 'center', letterSpacing: '0.1em' }}>
              {error}
            </div>
          )}

          {isRegister && (
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="FULL NAME"
              style={inputStyle}
              required
            />
          )}

          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="EMAIL"
            style={inputStyle}
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="PASSWORD"
            style={inputStyle}
            required
          />

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '14px',
              background: '#e8e4df',
              color: '#000',
              fontSize: '13px',
              letterSpacing: '0.2em',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              textTransform: 'uppercase',
              border: 'none',
              cursor: 'pointer',
              opacity: loading ? 0.5 : 1,
              transition: 'opacity 0.2s',
            }}
          >
            {loading ? '...' : isRegister ? 'Create Account' : 'Enter'}
          </button>

          <p className="text-center" style={{ fontSize: '12px', letterSpacing: '0.1em', color: '#6b6560' }}>
            {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button
              type="button"
              onClick={() => setIsRegister(!isRegister)}
              style={{ color: '#e8e4df', background: 'none', border: 'none', cursor: 'pointer', fontSize: '12px', letterSpacing: '0.1em' }}
            >
              {isRegister ? 'Sign In' : 'Register'}
            </button>
          </p>
        </form>
      </div>
    </div>
  )
}

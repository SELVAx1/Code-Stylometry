import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import GroupDetail from './pages/GroupDetail'
import StudentDetail from './pages/StudentDetail'
import SubmissionDetail from './pages/SubmissionDetail'
import Monitor from './pages/Monitor'

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token')
  if (!token) return <Navigate to="/login" />
  return children
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="monitor" element={<Monitor />} />
        <Route path="groups/:groupId" element={<GroupDetail />} />
        <Route path="students/:studentId" element={<StudentDetail />} />
        <Route path="submissions/:submissionId" element={<SubmissionDetail />} />
      </Route>
    </Routes>
  )
}

export default App

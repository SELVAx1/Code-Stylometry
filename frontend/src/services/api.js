import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error)
  }
)

export const auth = {
  login: (email, password) =>
    api.post('/auth/login', new URLSearchParams({ username: email, password })),
  register: (data) => api.post('/auth/register', data),
}

export const groups = {
  list: () => api.get('/groups/'),
  get: (id) => api.get(`/groups/${id}`),
  create: (name) => api.post('/groups/', { name }),
  addStudent: (groupId, data) => api.post(`/groups/${groupId}/students`, data),
  listStudents: (groupId) => api.get(`/groups/${groupId}/students`),
}

export const submissions = {
  collect: (studentId, limit = 200) =>
    api.post('/submissions/collect', { student_id: studentId, limit }),
  collectGroup: (groupId, limit = 200) =>
    api.post('/submissions/collect-group', { group_id: groupId, limit }),
  getByStudent: (studentId) => api.get(`/submissions/student/${studentId}`),
  getCount: (studentId) => api.get(`/submissions/student/${studentId}/count`),
  getDetail: (submissionId) => api.get(`/submissions/detail/${submissionId}`),
}

export const analysis = {
  buildProfile: (studentId) =>
    api.post('/analysis/build-profile', { student_id: studentId }),
  analyzeSubmission: (submissionId) =>
    api.post('/analysis/analyze-submission', { submission_id: submissionId }),
  getResults: (studentId) => api.get(`/analysis/results/${studentId}`),
  getGroupSummary: (groupId) => api.get(`/analysis/group-summary/${groupId}`),
}

export const monitor = {
  status: () => api.get('/monitor/status'),
  start: () => api.post('/monitor/start'),
  stop: () => api.post('/monitor/stop'),
  pollNow: () => api.post('/monitor/poll-now'),
  pending: () => api.get('/monitor/pending'),
  alerts: () => api.get('/monitor/recent-alerts'),
  activity: () => api.get('/monitor/activity'),
  cfLogin: (handleOrEmail, password) =>
    api.post('/monitor/cf-login', { handle_or_email: handleOrEmail, password }),
  cfSession: () => api.get('/monitor/cf-session'),
  fetchPending: () => api.post('/monitor/fetch-pending'),
}

export default api

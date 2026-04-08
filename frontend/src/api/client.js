import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Unknown error'
    return Promise.reject(new Error(msg))
  }
)

export const emailsApi = {
  list: (params = {}) => api.get('/emails', { params }).then((r) => r.data),
  get: (id) => api.get(`/emails/${id}`).then((r) => r.data),
}

export const envApi = {
  reset: (emailId = null) =>
    api.post('/reset', null, { params: emailId ? { email_id: emailId } : {} }).then((r) => r.data),
  step: (action) => api.post('/step', action).then((r) => r.data),
  state: () => api.get('/state').then((r) => r.data),
  tasks: () => api.get('/tasks').then((r) => r.data),
  health: () => api.get('/health').then((r) => r.data),
  agentStatus: () => api.get('/agent/status').then((r) => r.data),
  triage: (subject, body, sender = '') =>
    api.post('/triage', { subject, body, sender }, { timeout: 90000 }).then((r) => r.data),
}

export default api

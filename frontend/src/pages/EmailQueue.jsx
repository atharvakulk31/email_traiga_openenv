import { useState, useEffect, useMemo } from 'react'
import { Search, Filter, RefreshCw, Inbox, Mail } from 'lucide-react'
import { emailsApi } from '../api/client'
import EmailCard from '../components/EmailCard'
import { PageLoader } from '../components/LoadingSpinner'

const CATEGORIES = ['All', 'Billing Refund', 'Account', 'Feature Request', 'Technical Support']
const PRIORITIES = ['All', 'High', 'Medium', 'Low']

const CATEGORY_COUNTS_COLOR = {
  'Billing Refund':    'text-amber-400',
  'Account':           'text-purple-400',
  'Feature Request':   'text-cyan-400',
  'Technical Support': 'text-red-400',
}

export default function EmailQueue() {
  const [emails, setEmails]     = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)
  const [search, setSearch]     = useState('')
  const [category, setCategory] = useState('All')
  const [priority, setPriority] = useState('All')
  const [refreshing, setRefreshing] = useState(false)

  const fetchEmails = async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true)
    else setLoading(true)
    try {
      const data = await emailsApi.list()
      setEmails(data.emails)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => { fetchEmails() }, [])

  const filtered = useMemo(() => {
    return emails.filter((e) => {
      const matchSearch =
        !search ||
        e.subject.toLowerCase().includes(search.toLowerCase()) ||
        e.sender.toLowerCase().includes(search.toLowerCase()) ||
        e.body.toLowerCase().includes(search.toLowerCase())
      const matchCat  = category === 'All' || e.category === category
      const matchPri  = priority === 'All' || e.priority === priority
      return matchSearch && matchCat && matchPri
    })
  }, [emails, search, category, priority])

  // Stats
  const stats = useMemo(() => {
    const byPriority = { High: 0, Medium: 0, Low: 0 }
    emails.forEach((e) => { byPriority[e.priority] = (byPriority[e.priority] || 0) + 1 })
    return byPriority
  }, [emails])

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-blue-600/20 rounded-lg flex items-center justify-center">
              <Inbox size={18} className="text-blue-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Email Queue</h1>
              <p className="text-xs text-gray-500">Incoming support emails awaiting triage</p>
            </div>
          </div>
          <button
            onClick={() => fetchEmails(true)}
            disabled={refreshing}
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {[
          { label: 'High Priority', count: stats.High,   color: 'text-red-400',     bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'Medium',        count: stats.Medium, color: 'text-amber-400',   bg: 'bg-amber-500/10 border-amber-500/20' },
          { label: 'Low Priority',  count: stats.Low,    color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
        ].map(({ label, count, color, bg }) => (
          <div key={label} className={`card border ${bg} px-4 py-3`}>
            <p className={`text-2xl font-bold ${color}`}>{count}</p>
            <p className="text-xs text-gray-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="card p-4 mb-4">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="Search by subject, sender, or content…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-9 text-sm"
            />
          </div>

          {/* Category filter */}
          <div className="relative">
            <Filter size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="input pl-8 text-sm pr-8 appearance-none w-full sm:w-48"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c === 'All' ? 'All Categories' : c}</option>
              ))}
            </select>
          </div>

          {/* Priority filter */}
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="input text-sm appearance-none sm:w-36"
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>{p === 'All' ? 'All Priorities' : p}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Email List */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-12">
            <PageLoader text="Loading emails…" />
          </div>
        ) : error ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
              <Mail size={20} className="text-red-400" />
            </div>
            <p className="text-red-400 font-medium mb-1">Failed to load emails</p>
            <p className="text-gray-500 text-sm">{error}</p>
            <button onClick={() => fetchEmails()} className="btn-primary mt-4 text-sm">
              Try Again
            </button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-3">
              <Search size={20} className="text-gray-600" />
            </div>
            <p className="text-gray-400 font-medium">No emails match your filters</p>
            <button
              onClick={() => { setSearch(''); setCategory('All'); setPriority('All') }}
              className="btn-secondary mt-4 text-sm"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <div>
            <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
              <span className="text-xs text-gray-500">
                {filtered.length} of {emails.length} emails
              </span>
            </div>
            {filtered.map((email) => (
              <EmailCard key={email.id} email={email} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

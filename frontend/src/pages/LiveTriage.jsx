import { useState } from 'react'
import { envApi } from '../api/client'
import { Zap, Send, RotateCcw, CheckCircle, AlertCircle, Clock } from 'lucide-react'

const CATEGORY_COLORS = {
  'Billing Refund':    'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  'Account':           'bg-blue-500/10 text-blue-400 border-blue-500/30',
  'Feature Request':   'bg-purple-500/10 text-purple-400 border-purple-500/30',
  'Technical Support': 'bg-red-500/10 text-red-400 border-red-500/30',
}

const PRIORITY_COLORS = {
  High:   'bg-red-500/10 text-red-400 border-red-500/30',
  Medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  Low:    'bg-green-500/10 text-green-400 border-green-500/30',
}

const EXAMPLES = [
  {
    label: 'Billing issue',
    subject: 'Charged twice this month - need refund urgently',
    sender: 'customer@example.com',
    body: "Hi, I just noticed that my credit card was charged twice for my monthly subscription this month — both charges appeared on March 14th. I only have one active account and never authorized two payments. Please refund the duplicate charge immediately and confirm this won't happen again.",
  },
  {
    label: 'Account locked',
    subject: 'Cannot login - account locked, presentation in 2 hours',
    sender: 'user@company.com',
    body: "I've been locked out of my account after too many failed login attempts this morning. This is a critical emergency — I have a major client presentation in 2 hours and all my project files are in the platform. I need access restored immediately. Please help.",
  },
  {
    label: 'Feature request',
    subject: 'Feature Request: Export reports to PDF',
    sender: 'poweruser@startup.io',
    body: "I love using your platform but would really benefit from a PDF export option for the analytics reports. Right now I have to take screenshots which is tedious. A one-click PDF export would save me a lot of time each week. Hope this makes it onto the roadmap!",
  },
  {
    label: 'Bug report',
    subject: 'App crashes when opening large files',
    sender: 'dev@techcorp.dev',
    body: "Every time I try to open a file larger than 50MB the application crashes completely. This happens consistently on both my Mac and Windows machines. The bug is blocking my entire workflow as most of my project files are 60-100MB. Please fix this as soon as possible.",
  },
]

export default function LiveTriage() {
  const [subject, setSubject] = useState('')
  const [sender, setSender]   = useState('')
  const [body, setBody]       = useState('')
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)
  const [elapsed, setElapsed] = useState(null)

  const handleSubmit = async () => {
    const s = subject.trim()
    const b = body.trim()
    if (!s) { setError('Please enter a subject line.'); return }
    if (!b || b.length < 10) { setError('Please enter the email body (at least 10 characters).'); return }
    setLoading(true)
    setError(null)
    setResult(null)
    const t0 = Date.now()
    try {
      const data = await envApi.triage(s, b, sender.trim())
      setResult(data)
      setElapsed(((Date.now() - t0) / 1000).toFixed(2))
    } catch (e) {
      const msg = e.message || 'Unknown error'
      if (msg.includes('timeout') || msg.includes('Network'))
        setError('Request timed out. The LLM may be warming up — please try again in a few seconds.')
      else
        setError(`Triage failed: ${msg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleExample = (ex) => {
    setSubject(ex.subject)
    setSender(ex.sender)
    setBody(ex.body)
    setResult(null)
    setError(null)
  }

  const handleReset = () => {
    setSubject(''); setSender(''); setBody('')
    setResult(null); setError(null); setElapsed(null)
  }

  const scoreColor = result
    ? result.score >= 0.9 ? 'text-emerald-400'
    : result.score >= 0.7 ? 'text-yellow-400'
    : 'text-red-400'
    : ''

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-1">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Zap size={16} className="text-white" />
          </div>
          <h1 className="text-xl font-bold text-white">Live AI Triage</h1>
        </div>
        <p className="text-gray-400 text-sm ml-11">
          Paste any real email — GPT-4o-mini classifies, prioritizes, and drafts a reply instantly.
        </p>
      </div>

      {/* Quick examples */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Quick Examples</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex.label}
              onClick={() => handleExample(ex)}
              className="px-3 py-1.5 text-xs bg-gray-800 text-gray-300 rounded-lg border border-gray-700 hover:border-blue-500/50 hover:text-blue-400 transition-colors"
            >
              {ex.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input panel */}
        <div className="space-y-4">
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-4">
            <p className="text-sm font-semibold text-gray-300">Email Input</p>

            <div>
              <label className="block text-xs text-gray-500 mb-1">Subject *</label>
              <input
                value={subject}
                onChange={e => setSubject(e.target.value)}
                placeholder="e.g. Cannot login - account locked"
                className="w-full bg-gray-800 text-white text-sm rounded-lg px-3 py-2.5 border border-gray-700 focus:border-blue-500 focus:outline-none placeholder-gray-600"
              />
            </div>

            <div>
              <label className="block text-xs text-gray-500 mb-1">Sender (optional)</label>
              <input
                value={sender}
                onChange={e => setSender(e.target.value)}
                placeholder="e.g. customer@company.com"
                className="w-full bg-gray-800 text-white text-sm rounded-lg px-3 py-2.5 border border-gray-700 focus:border-blue-500 focus:outline-none placeholder-gray-600"
              />
            </div>

            <div>
              <label className="block text-xs text-gray-500 mb-1">Email Body *</label>
              <textarea
                value={body}
                onChange={e => setBody(e.target.value)}
                placeholder="Paste the email body here..."
                rows={8}
                className="w-full bg-gray-800 text-white text-sm rounded-lg px-3 py-2.5 border border-gray-700 focus:border-blue-500 focus:outline-none placeholder-gray-600 resize-none"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleSubmit}
                disabled={loading || !subject.trim() || !body.trim()}
                className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Send size={15} />
                    Triage Email
                  </>
                )}
              </button>
              <button
                onClick={handleReset}
                className="px-3 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg border border-gray-700 transition-colors"
                title="Clear"
              >
                <RotateCcw size={15} />
              </button>
            </div>
          </div>
        </div>

        {/* Result panel */}
        <div>
          {!result && !loading && !error && (
            <div className="bg-gray-900 rounded-xl border border-gray-800 h-full flex items-center justify-center p-10">
              <div className="text-center space-y-2">
                <div className="w-12 h-12 bg-gray-800 rounded-full flex items-center justify-center mx-auto">
                  <Zap size={20} className="text-gray-600" />
                </div>
                <p className="text-gray-500 text-sm">Results will appear here</p>
                <p className="text-gray-600 text-xs">Paste an email and click Triage</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="bg-gray-900 rounded-xl border border-gray-800 h-full flex items-center justify-center p-10">
              <div className="text-center space-y-3">
                <div className="w-12 h-12 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto" />
                <p className="text-gray-400 text-sm">GPT-4o-mini is analyzing your email...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-500/5 rounded-xl border border-red-500/20 p-5 flex gap-3">
              <AlertCircle size={18} className="text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-red-400 text-sm font-medium">Triage failed</p>
                <p className="text-red-400/70 text-xs mt-1">{error}</p>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {/* Score banner */}
              <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm font-semibold text-gray-300">Triage Result</p>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Clock size={12} />
                    {elapsed}s
                  </div>
                </div>

                <div className="flex gap-3 mb-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${CATEGORY_COLORS[result.category] || 'bg-gray-700 text-gray-300 border-gray-600'}`}>
                    {result.category}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${PRIORITY_COLORS[result.priority] || 'bg-gray-700 text-gray-300 border-gray-600'}`}>
                    {result.priority} Priority
                  </span>
                </div>

                {/* Score bar */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">Reply Quality Score</span>
                    <span className={`text-sm font-bold ${scoreColor}`}>
                      {(result.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${
                        result.score >= 0.9 ? 'bg-emerald-500' :
                        result.score >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${result.score * 100}%` }}
                    />
                  </div>
                </div>

                {/* Reply checks */}
                {result.breakdown?.reply?.detail && (
                  <div className="mt-4 grid grid-cols-2 gap-2">
                    {Object.entries(result.breakdown.reply.detail).map(([check, passed]) => (
                      <div key={check} className="flex items-center gap-2">
                        {passed
                          ? <CheckCircle size={13} className="text-emerald-400 flex-shrink-0" />
                          : <AlertCircle size={13} className="text-red-400 flex-shrink-0" />
                        }
                        <span className="text-xs text-gray-400 capitalize">
                          {check.replace(/_/g, ' ')}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Generated reply */}
              <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  AI-Generated Reply
                </p>
                <p className="text-gray-300 text-sm whitespace-pre-wrap leading-relaxed">
                  {result.reply}
                </p>
              </div>

              {/* Model badge */}
              <div className="flex items-center gap-2 px-3 py-2 bg-gray-900 rounded-lg border border-gray-800">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                <span className="text-xs text-gray-500">
                  Powered by <span className="text-emerald-400 font-medium">{result.breakdown?.model || 'GPT-4o-mini'}</span> via OpenAI
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

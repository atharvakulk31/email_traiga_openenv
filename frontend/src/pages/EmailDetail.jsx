import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Mail, User, Clock, Tag, AlertCircle,
  Play, CheckCircle2, XCircle, ChevronDown, ChevronUp
} from 'lucide-react'
import { emailsApi, envApi } from '../api/client'
import { CategoryBadge, PriorityBadge, ScoreBadge } from '../components/Badge'
import { PageLoader } from '../components/LoadingSpinner'
import ScoreBar from '../components/ScoreBar'

const CATEGORIES = ['Billing Refund', 'Account', 'Feature Request', 'Technical Support']
const PRIORITIES = ['Low', 'Medium', 'High']

export default function EmailDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [email, setEmail]         = useState(null)
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult]       = useState(null)
  const [showBreakdown, setShowBreakdown] = useState(false)

  // Action form
  const [action, setAction] = useState({
    category: '',
    priority: '',
    reply: '',
  })

  useEffect(() => {
    emailsApi.get(id)
      .then(setEmail)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!action.category && !action.priority && !action.reply.trim()) return

    setSubmitting(true)
    setResult(null)
    try {
      await envApi.reset(id)
      const payload = {}
      if (action.category) payload.category = action.category
      if (action.priority) payload.priority = action.priority
      if (action.reply.trim()) payload.reply = action.reply.trim()
      const res = await envApi.step(payload)
      setResult(res)
      setShowBreakdown(true)
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="pt-8"><PageLoader text="Loading email…" /></div>

  if (error || !email) return (
    <div className="p-8 text-center">
      <XCircle size={40} className="text-red-400 mx-auto mb-3" />
      <p className="text-red-400 font-medium">{error || 'Email not found'}</p>
      <button onClick={() => navigate('/')} className="btn-secondary mt-4">← Back</button>
    </div>
  )

  const score = result?.reward?.score
  const explanation = result?.reward?.explanation
  const breakdown = result?.reward?.breakdown

  return (
    <div className="animate-fade-in max-w-4xl">
      {/* Back */}
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-gray-400 hover:text-gray-200 text-sm mb-6 transition-colors"
      >
        <ArrowLeft size={15} /> Back to Queue
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Email Content — 3 cols */}
        <div className="lg:col-span-3 space-y-4">
          {/* Email Card */}
          <div className="card p-5">
            <div className="flex items-start justify-between gap-3 mb-4">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 bg-blue-600/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Mail size={16} className="text-blue-400" />
                </div>
                <div>
                  <h2 className="font-semibold text-white text-base leading-snug">{email.subject}</h2>
                  <div className="flex items-center gap-1.5 mt-0.5 text-xs text-gray-500">
                    <User size={11} />
                    <span>{email.sender}</span>
                  </div>
                </div>
              </div>
              <div className="flex-shrink-0 text-xs text-gray-600 flex items-center gap-1">
                <Clock size={11} />
                {email.timestamp ? new Date(email.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}
              </div>
            </div>

            <div className="flex gap-2 mb-4">
              <CategoryBadge category={email.category} />
              <PriorityBadge priority={email.priority} />
            </div>

            <div className="bg-gray-800/60 rounded-lg p-4 text-sm text-gray-300 leading-relaxed whitespace-pre-wrap font-mono border border-gray-700/50">
              {email.body}
            </div>
          </div>

          {/* Ground Truth */}
          <div className="card p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Ground Truth Labels
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-800/50 rounded-lg p-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <Tag size={11} className="text-gray-500" />
                  <span className="text-xs text-gray-500">Category</span>
                </div>
                <CategoryBadge category={email.category} />
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <AlertCircle size={11} className="text-gray-500" />
                  <span className="text-xs text-gray-500">Priority</span>
                </div>
                <PriorityBadge priority={email.priority} />
              </div>
            </div>
          </div>
        </div>

        {/* Action Panel — 2 cols */}
        <div className="lg:col-span-2 space-y-4">
          <div className="card p-5">
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
              <Play size={15} className="text-blue-400" />
              Triage Action
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Category */}
              <div>
                <label className="label">Category</label>
                <select
                  value={action.category}
                  onChange={(e) => setAction((a) => ({ ...a, category: e.target.value }))}
                  className="input text-sm appearance-none"
                >
                  <option value="">— Select category —</option>
                  {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              {/* Priority */}
              <div>
                <label className="label">Priority</label>
                <div className="flex gap-2">
                  {PRIORITIES.map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setAction((a) => ({ ...a, priority: p }))}
                      className={`flex-1 py-2 rounded-lg text-xs font-medium border transition-colors ${
                        action.priority === p
                          ? p === 'High'   ? 'bg-red-600/30 border-red-500 text-red-400'
                          : p === 'Medium' ? 'bg-amber-600/30 border-amber-500 text-amber-400'
                          :                  'bg-emerald-600/30 border-emerald-500 text-emerald-400'
                          : 'bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              {/* Reply */}
              <div>
                <label className="label">Reply Draft</label>
                <textarea
                  value={action.reply}
                  onChange={(e) => setAction((a) => ({ ...a, reply: e.target.value }))}
                  placeholder="Write a professional support reply…"
                  rows={6}
                  className="input text-sm resize-none leading-relaxed"
                />
              </div>

              <button
                type="submit"
                disabled={submitting || (!action.category && !action.priority && !action.reply.trim())}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Evaluating…
                  </>
                ) : (
                  <>
                    <Play size={14} />
                    Submit & Evaluate
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Result Panel */}
          {result && (
            <div className={`card p-5 animate-fade-in border ${
              result.error ? 'border-red-500/30' :
              score >= 0.7  ? 'border-emerald-500/30' :
              score >= 0.4  ? 'border-amber-500/30' :
                              'border-red-500/30'
            }`}>
              {result.error ? (
                <div className="flex items-center gap-2 text-red-400">
                  <XCircle size={16} />
                  <span className="text-sm">{result.error}</span>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {score >= 0.7
                        ? <CheckCircle2 size={16} className="text-emerald-400" />
                        : <XCircle size={16} className="text-amber-400" />
                      }
                      <span className="font-semibold text-white text-sm">Evaluation Result</span>
                    </div>
                    <ScoreBadge score={score} />
                  </div>

                  <ScoreBar score={score} />

                  <div className="mt-3">
                    <p className="text-xs text-gray-400 leading-relaxed">{explanation}</p>
                  </div>

                  {/* Breakdown */}
                  {breakdown && (
                    <div className="mt-3">
                      <button
                        onClick={() => setShowBreakdown((s) => !s)}
                        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition-colors"
                      >
                        {showBreakdown ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                        Score breakdown
                      </button>

                      {showBreakdown && (
                        <div className="mt-2 space-y-2 animate-fade-in">
                          {breakdown.category && (
                            <BreakdownRow
                              label="Category"
                              predicted={breakdown.category.predicted}
                              expected={breakdown.category.expected}
                              score={breakdown.category.score}
                              weight={0.5}
                            />
                          )}
                          {breakdown.priority && (
                            <BreakdownRow
                              label="Priority"
                              predicted={breakdown.priority.predicted}
                              expected={breakdown.priority.expected}
                              score={breakdown.priority.score}
                              weight={0.3}
                            />
                          )}
                          {breakdown.reply && (
                            <div className="bg-gray-800/60 rounded-lg p-3">
                              <div className="flex justify-between items-center mb-2">
                                <span className="text-xs font-medium text-gray-300">Reply Quality</span>
                                <span className="text-xs text-gray-500">{(breakdown.reply.score * 0.2).toFixed(3)} pts</span>
                              </div>
                              {Object.entries(breakdown.reply.detail || {}).map(([k, v]) => (
                                <div key={k} className="flex items-center gap-2 py-0.5">
                                  {v
                                    ? <CheckCircle2 size={11} className="text-emerald-400 flex-shrink-0" />
                                    : <XCircle size={11} className="text-red-400 flex-shrink-0" />
                                  }
                                  <span className="text-xs text-gray-400">{formatCheckKey(k)}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function BreakdownRow({ label, predicted, expected, score, weight }) {
  const correct = score === 1.0
  const partial  = score > 0 && score < 1
  return (
    <div className="bg-gray-800/60 rounded-lg p-3 flex items-center justify-between">
      <div className="min-w-0">
        <p className="text-xs font-medium text-gray-300">{label}</p>
        <p className="text-xs text-gray-500 mt-0.5">
          Predicted: <span className="text-gray-300">{predicted}</span>
          {' · '}Expected: <span className="text-gray-300">{expected}</span>
        </p>
      </div>
      <div className="flex items-center gap-2 ml-3 flex-shrink-0">
        {correct
          ? <CheckCircle2 size={13} className="text-emerald-400" />
          : partial
          ? <AlertCircle size={13} className="text-amber-400" />
          : <XCircle size={13} className="text-red-400" />
        }
        <span className="text-xs text-gray-400">×{weight} = {(score * weight).toFixed(3)}</span>
      </div>
    </div>
  )
}

function formatCheckKey(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

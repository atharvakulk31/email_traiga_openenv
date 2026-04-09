import { useState, useEffect } from 'react'
import {
  BarChart3, TrendingUp, Award, Target,
  CheckCircle2, XCircle, AlertCircle, Layers, Play, Sparkles
} from 'lucide-react'
import {
  RadialBarChart, RadialBar, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import { emailsApi, envApi } from '../api/client'
import { CategoryBadge, PriorityBadge, ScoreBadge, DifficultyBadge } from '../components/Badge'
import { PageLoader } from '../components/LoadingSpinner'
import ScoreBar from '../components/ScoreBar'

const PIE_COLORS = ['#f59e0b', '#a78bfa', '#22d3ee', '#f87171']

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)) }

const TASK_META = [
  { id: 'task_1', name: 'Classification', difficulty: 'Easy',   description: 'Correctly identify email category', weight: 0.5, grader: 'easy_grader' },
  { id: 'task_2', name: 'Priority',       difficulty: 'Medium', description: 'Detect urgency level (partial credit)', weight: 0.3, grader: 'medium_grader' },
  { id: 'task_3', name: 'Reply Quality',  difficulty: 'Hard',   description: 'Draft a professional support reply', weight: 0.2, grader: 'hard_grader' },
]

export default function EvaluationDashboard() {
  const [emails, setEmails]       = useState([])
  const [tasks, setTasks]         = useState([])
  const [results, setResults]     = useState([])
  const [running, setRunning]     = useState(false)
  const [progress, setProgress]   = useState(0)
  const [error, setError]         = useState(null)
  const [loaded, setLoaded]       = useState(false)
  const [agentStatus, setAgentStatus] = useState(null)

  useEffect(() => {
    Promise.all([emailsApi.list(), envApi.tasks(), envApi.agentStatus().catch(() => null)])
      .then(([emailData, taskData, statusData]) => {
        setEmails(emailData.emails)
        setTasks(taskData)
        setAgentStatus(statusData)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoaded(true))
  }, [])

  const runFullEval = async () => {
    if (running || emails.length === 0) return
    setRunning(true)
    setResults([])
    setProgress(0)
    setError(null)

    const newResults = []
    try {
      for (let i = 0; i < emails.length; i++) {
        const email = emails[i]
        await envApi.reset(email.id)
        // Use real HuggingFace model via /api/triage
        const triageRes = await envApi.triage(email.subject, email.body, email.sender || '')
        const action = {
          category: triageRes.category,
          priority: triageRes.priority,
          reply:    triageRes.reply,
        }
        const stepRes = await envApi.step(action)

        newResults.push({
          email,
          action,
          // reward field is now a float (openenv-core compliant);
          // rich detail (score/explanation/breakdown) is in reward_detail
          reward: stepRes.reward_detail || { score: stepRes.reward, explanation: '', breakdown: {} },
        })
        setResults([...newResults])
        setProgress(Math.round(((i + 1) / emails.length) * 100))
        await sleep(120)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setRunning(false)
    }
  }

  // --- Derived stats ---
  const avgScore = results.length
    ? results.reduce((s, r) => s + r.reward.score, 0) / results.length
    : 0

  const catAccuracy = results.length
    ? results.filter((r) => r.action.category === r.email.category).length / results.length
    : 0

  const priAccuracy = results.length
    ? results.filter((r) => r.action.priority === r.email.priority).length / results.length
    : 0

  const passRate = results.length
    ? results.filter((r) => r.reward.score >= 0.7).length / results.length
    : 0

  // Per-category breakdown
  const categoryBreakdown = Object.entries(
    results.reduce((acc, r) => {
      const cat = r.email.category
      if (!acc[cat]) acc[cat] = { total: 0, correct: 0, scoreSum: 0 }
      acc[cat].total++
      acc[cat].scoreSum += r.reward.score
      if (r.action.category === cat) acc[cat].correct++
      return acc
    }, {})
  ).map(([cat, data]) => ({
    name: cat.split(' ')[0],   // short label for chart
    fullName: cat,
    accuracy: data.total ? Math.round((data.correct / data.total) * 100) : 0,
    avgScore: data.total ? data.scoreSum / data.total : 0,
    count: data.total,
  }))

  // Category distribution (pie)
  const categoryDist = Object.entries(
    emails.reduce((acc, e) => {
      acc[e.category] = (acc[e.category] || 0) + 1
      return acc
    }, {})
  ).map(([name, value]) => ({ name, value }))

  // Score distribution (bar)
  const scoreDist = [
    { range: '0–0.3', count: results.filter((r) => r.reward.score < 0.3).length },
    { range: '0.3–0.5', count: results.filter((r) => r.reward.score >= 0.3 && r.reward.score < 0.5).length },
    { range: '0.5–0.7', count: results.filter((r) => r.reward.score >= 0.5 && r.reward.score < 0.7).length },
    { range: '0.7–0.9', count: results.filter((r) => r.reward.score >= 0.7 && r.reward.score < 0.9).length },
    { range: '0.9–1.0', count: results.filter((r) => r.reward.score >= 0.9).length },
  ]

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload?.length) {
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs">
          <p className="text-gray-300">{payload[0].name || payload[0].dataKey}</p>
          <p className="text-white font-bold">{payload[0].value}</p>
        </div>
      )
    }
    return null
  }

  if (!loaded) return <div className="pt-8"><PageLoader text="Loading evaluation data…" /></div>

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-600/20 rounded-lg flex items-center justify-center">
            <BarChart3 size={18} className="text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Evaluation Dashboard</h1>
            <div className="flex items-center gap-2 mt-0.5">
              <p className="text-xs text-gray-500">Full-dataset agent performance</p>
              {agentStatus && (
                <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border ${
                  agentStatus.ready
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                    : 'bg-gray-500/10 border-gray-500/30 text-gray-500'
                }`}>
                  <Sparkles size={10} />
                  {agentStatus.ready ? agentStatus.model.split('/').pop() : 'Rule-based'}
                </span>
              )}
            </div>
          </div>
        </div>
        <button
          onClick={runFullEval}
          disabled={running}
          className="btn-primary flex items-center gap-2 text-sm"
        >
          {running
            ? <><div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />Evaluating…</>
            : <><Play size={13} />Run Full Evaluation</>
          }
        </button>
      </div>

      {/* Progress bar (while running) */}
      {running && (
        <div className="card p-4 mb-4 animate-fade-in">
          <div className="flex justify-between text-xs text-gray-400 mb-2">
            <span>Evaluating emails… ({results.length}/{emails.length})</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {error && (
        <div className="card p-4 mb-4 border border-red-500/30 flex items-center gap-2 text-red-400 text-sm">
          <XCircle size={15} /> {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {[
          {
            label: 'Avg Score',
            value: results.length ? `${(avgScore * 100).toFixed(1)}%` : '—',
            icon: TrendingUp,
            color: avgScore >= 0.7 ? 'text-emerald-400' : avgScore >= 0.4 ? 'text-amber-400' : 'text-red-400',
            bg: 'bg-emerald-500/10 border-emerald-500/20',
          },
          {
            label: 'Category Acc.',
            value: results.length ? `${(catAccuracy * 100).toFixed(1)}%` : '—',
            icon: Target,
            color: 'text-blue-400',
            bg: 'bg-blue-500/10 border-blue-500/20',
          },
          {
            label: 'Priority Acc.',
            value: results.length ? `${(priAccuracy * 100).toFixed(1)}%` : '—',
            icon: Award,
            color: 'text-purple-400',
            bg: 'bg-purple-500/10 border-purple-500/20',
          },
          {
            label: 'Pass Rate (≥70%)',
            value: results.length ? `${(passRate * 100).toFixed(1)}%` : '—',
            icon: CheckCircle2,
            color: passRate >= 0.7 ? 'text-emerald-400' : 'text-amber-400',
            bg: 'bg-amber-500/10 border-amber-500/20',
          },
        ].map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className={`card border ${bg} px-4 py-4`}>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-gray-500">{label}</p>
              <Icon size={14} className={color} />
            </div>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-gray-600 mt-0.5">
              {results.length ? `${results.length} emails` : 'Run evaluation first'}
            </p>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      {results.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          {/* Score Distribution */}
          <div className="card p-5">
            <h3 className="font-semibold text-white text-sm mb-4">Score Distribution</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={scoreDist} barSize={32}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="range" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: '#1f2937' }} />
                <Bar dataKey="count" name="Emails" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Category Distribution Pie */}
          <div className="card p-5">
            <h3 className="font-semibold text-white text-sm mb-4">Email Category Mix</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={categoryDist}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {categoryDist.map((entry, i) => (
                    <Cell key={entry.name} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: '8px', fontSize: '12px' }}
                  itemStyle={{ color: '#e5e7eb' }}
                />
                <Legend
                  formatter={(v) => <span style={{ color: '#9ca3af', fontSize: '11px' }}>{v}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Category Accuracy Table */}
      {categoryBreakdown.length > 0 && (
        <div className="card p-5 mb-6">
          <h3 className="font-semibold text-white text-sm mb-4">Per-Category Performance</h3>
          <div className="space-y-3">
            {categoryBreakdown.map((row) => (
              <div key={row.fullName} className="flex items-center gap-4">
                <div className="w-36 flex-shrink-0">
                  <CategoryBadge category={row.fullName} />
                </div>
                <div className="flex-1">
                  <ScoreBar score={row.accuracy / 100} showLabel={false} height="h-1.5" />
                </div>
                <div className="text-xs text-gray-400 w-12 text-right">{row.accuracy}%</div>
                <div className="text-xs text-gray-600 w-16 text-right">{row.count} emails</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tasks Info */}
      <div className="card p-5 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Layers size={15} className="text-gray-400" />
          <h3 className="font-semibold text-white text-sm">Task Specifications</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {TASK_META.map((task) => (
            <div key={task.id} className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50">
              <div className="flex items-start justify-between mb-2">
                <p className="font-semibold text-white text-sm">{task.name}</p>
                <DifficultyBadge difficulty={task.difficulty} />
              </div>
              <p className="text-xs text-gray-400 leading-relaxed mb-3">{task.description}</p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-600">Weight</span>
                <span className="text-xs font-bold text-blue-400">{(task.weight * 100).toFixed(0)}%</span>
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-xs text-gray-600">Grader</span>
                <span className="text-xs font-mono text-gray-500">{task.grader}</span>
              </div>
              {results.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Performance</span>
                    <span className="text-xs font-bold text-white">
                      {task.id === 'task_1'
                        ? `${(catAccuracy * 100).toFixed(1)}%`
                        : task.id === 'task_2'
                        ? `${(priAccuracy * 100).toFixed(1)}%`
                        : `${(avgScore * 100).toFixed(1)}% (avg)`
                      }
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Results Table */}
      {results.length > 0 && (
        <div className="card overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
            <h3 className="font-semibold text-white text-sm">Per-Email Results</h3>
            <span className="text-xs text-gray-500">{results.length} evaluated</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
                  <th className="text-left px-5 py-3 font-medium">Subject</th>
                  <th className="text-left px-4 py-3 font-medium">Predicted</th>
                  <th className="text-left px-4 py-3 font-medium">Expected</th>
                  <th className="text-left px-4 py-3 font-medium">Priority</th>
                  <th className="text-right px-5 py-3 font-medium">Score</th>
                </tr>
              </thead>
              <tbody>
                {results.map(({ email, action, reward }) => {
                  const catCorrect = action.category === email.category
                  const priCorrect = action.priority === email.priority
                  return (
                    <tr key={email.id} className="border-b border-gray-800/60 hover:bg-gray-800/30 transition-colors">
                      <td className="px-5 py-3">
                        <p className="text-gray-200 text-xs font-medium truncate max-w-[200px]">{email.subject}</p>
                        <p className="text-gray-600 text-xs mt-0.5">{email.id}</p>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          {catCorrect
                            ? <CheckCircle2 size={11} className="text-emerald-400 flex-shrink-0" />
                            : <XCircle size={11} className="text-red-400 flex-shrink-0" />
                          }
                          <span className="text-xs text-gray-300 truncate max-w-[110px]">{action.category}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <CategoryBadge category={email.category} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          {priCorrect
                            ? <CheckCircle2 size={11} className="text-emerald-400 flex-shrink-0" />
                            : <AlertCircle size={11} className="text-amber-400 flex-shrink-0" />
                          }
                          <PriorityBadge priority={email.priority} />
                        </div>
                      </td>
                      <td className="px-5 py-3 text-right">
                        <ScoreBadge score={reward.score} />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!running && results.length === 0 && (
        <div className="card p-12 text-center">
          <div className="w-14 h-14 bg-blue-600/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <BarChart3 size={24} className="text-blue-400" />
          </div>
          <p className="text-white font-semibold mb-1">No evaluation data yet</p>
          <p className="text-gray-500 text-sm mb-5">
            Click "Run Full Evaluation" to benchmark the AI agent across all {emails.length} emails.
          </p>
          <button onClick={runFullEval} className="btn-primary inline-flex items-center gap-2">
            <Play size={14} /> Run Full Evaluation
          </button>
        </div>
      )}
    </div>
  )
}

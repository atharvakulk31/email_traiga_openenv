import { useState, useEffect, useRef } from 'react'
import {
  Bot, Play, RotateCcw, CheckCircle2, XCircle,
  AlertCircle, Cpu, Zap, Sparkles
} from 'lucide-react'
import { emailsApi, envApi } from '../api/client'
import { CategoryBadge, PriorityBadge, ScoreBadge } from '../components/Badge'
import ScoreBar from '../components/ScoreBar'

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

export default function AgentSimulation() {
  const [emails, setEmails]         = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [running, setRunning]       = useState(false)
  const [log, setLog]               = useState([])
  const [result, setResult]         = useState(null)
  const [currentEmail, setCurrentEmail] = useState(null)
  const [step, setStep]             = useState('')
  const [agentStatus, setAgentStatus]   = useState(null)
  const logRef = useRef(null)

  useEffect(() => {
    emailsApi.list().then((d) => setEmails(d.emails)).catch(() => {})
    envApi.agentStatus().then(setAgentStatus).catch(() => {})
  }, [])

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [log])

  const addLog = (msg, type = 'info') => {
    const ts = new Date().toLocaleTimeString()
    setLog((l) => [...l, { ts, msg, type }])
  }

  const runSimulation = async () => {
    if (running) return
    setRunning(true)
    setLog([])
    setResult(null)
    setCurrentEmail(null)

    try {
      // Step 1: Reset
      setStep('Resetting environment…')
      addLog('Initializing environment…', 'info')
      await sleep(400)

      const resetRes = await envApi.reset(selectedId || null)
      const obs = resetRes.observation
      addLog(`Environment reset. Loaded email: ${obs.email_id}`, 'success')
      addLog(`Subject: "${obs.subject}"`, 'info')
      addLog(`From: ${obs.sender}`, 'info')

      // Fetch full email for display
      const fullEmail = emails.find((e) => e.id === obs.email_id) || {
        id: obs.email_id,
        subject: obs.subject,
        body: obs.body,
        sender: obs.sender,
      }
      setCurrentEmail(fullEmail)
      await sleep(600)

      // Step 2: HuggingFace inference
      setStep('Running HuggingFace model…')
      addLog(`Calling HuggingFace model: ${agentStatus?.model || 'meta-llama/Meta-Llama-3.1-8B-Instruct'}…`, 'info')

      const triageRes = await envApi.triage(
        fullEmail.subject,
        fullEmail.body,
        fullEmail.sender || ''
      )
      const action = {
        category: triageRes.category,
        priority: triageRes.priority,
        reply:    triageRes.reply,
      }

      addLog(`Model: ${triageRes.breakdown?.model || agentStatus?.model || 'HuggingFace'}`, 'success')
      addLog(`Category prediction: "${action.category}"`, 'info')
      addLog(`Priority prediction: "${action.priority}"`, 'info')
      addLog(`Reply drafted (${action.reply.split(' ').length} words)`, 'info')
      await sleep(300)

      // Step 3: Submit to OpenEnv
      setStep('Submitting to environment…')
      addLog('Submitting action to OpenEnv environment…', 'info')
      await sleep(200)

      const stepRes = await envApi.step(action)
      const { reward } = stepRes
      addLog(`Score received: ${reward.score.toFixed(4)}`, reward.score >= 0.7 ? 'success' : 'warn')

      setResult({ action, reward: stepRes.reward, email: fullEmail })
      addLog('Simulation complete.', 'success')
    } catch (e) {
      addLog(`Error: ${e.message}`, 'error')
    } finally {
      setRunning(false)
      setStep('')
    }
  }

  const reset = () => {
    setLog([])
    setResult(null)
    setCurrentEmail(null)
    setStep('')
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-600/20 rounded-lg flex items-center justify-center">
            <Bot size={18} className="text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Agent Simulation</h1>
            <p className="text-xs text-gray-500">Run the AI agent against the triage environment</p>
          </div>
        </div>

        <div className="flex gap-2">
          {(log.length > 0 || result) && (
            <button onClick={reset} className="btn-secondary flex items-center gap-2 text-sm">
              <RotateCcw size={13} /> Reset
            </button>
          )}
          <button
            onClick={runSimulation}
            disabled={running}
            className="btn-primary flex items-center gap-2 text-sm"
          >
            {running
              ? <><div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Running…</>
              : <><Play size={13} /> Run Agent</>
            }
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Config */}
        <div className="lg:col-span-2 space-y-4">
          <div className="card p-5">
            <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2">
              <Cpu size={14} className="text-gray-400" />
              Configuration
            </h3>

            <div className="space-y-4">
              <div>
                <label className="label">Email to Process</label>
                <select
                  value={selectedId}
                  onChange={(e) => setSelectedId(e.target.value)}
                  disabled={running}
                  className="input text-sm appearance-none"
                >
                  <option value="">Random email</option>
                  {emails.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.id} — {e.subject.slice(0, 35)}{e.subject.length > 35 ? '…' : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Model</label>
                <div className={`input text-sm flex items-center gap-2 ${agentStatus?.ready ? 'text-gray-200' : 'text-gray-500'}`}>
                  <Sparkles size={13} className={agentStatus?.ready ? 'text-amber-400' : 'text-gray-600'} />
                  <span className="truncate">
                    {agentStatus?.model || 'Loading…'}
                  </span>
                </div>
                <p className="text-xs mt-1.5">
                  {agentStatus?.ready
                    ? <span className="text-emerald-400">HuggingFace LLM active</span>
                    : <span className="text-amber-400">Rule-based fallback — set HF_TOKEN for LLM</span>
                  }
                </p>
              </div>

              <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                <p className="text-xs text-blue-300 leading-relaxed">
                  The agent analyzes email content, predicts category & priority,
                  and drafts a professional reply — then receives a reward score.
                </p>
              </div>
            </div>
          </div>

          {/* Current Email Preview */}
          {currentEmail && (
            <div className="card p-4 animate-fade-in">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Active Email
              </p>
              <p className="text-sm font-medium text-white mb-1">{currentEmail.subject}</p>
              <p className="text-xs text-gray-500 mb-3">{currentEmail.sender}</p>
              {currentEmail.category && (
                <div className="flex gap-2">
                  <CategoryBadge category={currentEmail.category} />
                  <PriorityBadge priority={currentEmail.priority} />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Console + Result */}
        <div className="lg:col-span-3 space-y-4">
          {/* Console */}
          <div className="card overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span className="text-xs font-medium text-gray-400">Agent Console</span>
              </div>
              {running && step && (
                <span className="text-xs text-blue-400 flex items-center gap-1.5">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                  {step}
                </span>
              )}
            </div>

            <div
              ref={logRef}
              className="h-64 overflow-y-auto p-4 font-mono text-xs space-y-1 bg-gray-950/50"
            >
              {log.length === 0 ? (
                <p className="text-gray-600 italic">Press "Run Agent" to start simulation…</p>
              ) : (
                log.map((entry, i) => (
                  <div key={i} className="flex gap-3">
                    <span className="text-gray-600 flex-shrink-0">{entry.ts}</span>
                    <span className={
                      entry.type === 'success' ? 'text-emerald-400' :
                      entry.type === 'error'   ? 'text-red-400' :
                      entry.type === 'warn'    ? 'text-amber-400' :
                                                 'text-gray-300'
                    }>
                      {entry.msg}
                    </span>
                  </div>
                ))
              )}
              {running && (
                <div className="flex gap-3">
                  <span className="text-gray-600">…</span>
                  <span className="text-gray-500 animate-pulse">Processing</span>
                </div>
              )}
            </div>
          </div>

          {/* Result */}
          {result && (
            <div className="card p-5 animate-fade-in">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-white text-sm flex items-center gap-2">
                  <CheckCircle2 size={15} className="text-emerald-400" />
                  Simulation Result
                </h3>
                <ScoreBadge score={result.reward.score} />
              </div>

              <ScoreBar score={result.reward.score} />

              {/* Action summary */}
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="bg-gray-800/60 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">Predicted Category</p>
                  <CategoryBadge category={result.action.category} />
                </div>
                <div className="bg-gray-800/60 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">Predicted Priority</p>
                  <PriorityBadge priority={result.action.priority} />
                </div>
              </div>

              {/* Breakdown */}
              {result.reward.breakdown && (
                <div className="mt-4 space-y-2">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score Breakdown
                  </p>
                  {Object.entries(result.reward.breakdown).map(([key, val]) => (
                    <div key={key} className="bg-gray-800/50 rounded-lg p-3 flex items-center justify-between">
                      <div>
                        <p className="text-xs font-medium text-gray-300 capitalize">{key}</p>
                        {val.predicted !== undefined && (
                          <p className="text-xs text-gray-600 mt-0.5">
                            {val.predicted} → {val.expected}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {val.score === 1.0
                          ? <CheckCircle2 size={13} className="text-emerald-400" />
                          : val.score > 0
                          ? <AlertCircle size={13} className="text-amber-400" />
                          : <XCircle size={13} className="text-red-400" />
                        }
                        <span className="text-xs font-bold text-gray-300">
                          {val.score?.toFixed(2) ?? '—'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Reply preview */}
              {result.action.reply && (
                <div className="mt-4">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
                    Generated Reply
                  </p>
                  <div className="bg-gray-800/60 rounded-lg p-3 text-xs text-gray-300 leading-relaxed whitespace-pre-wrap max-h-40 overflow-y-auto border border-gray-700/50">
                    {result.action.reply}
                  </div>
                </div>
              )}

              <p className="text-xs text-gray-500 mt-4 leading-relaxed">
                {result.reward.explanation}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

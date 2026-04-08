const CATEGORY_STYLES = {
  'Billing Refund':    'bg-amber-500/15 text-amber-400 border-amber-500/30',
  'Account':           'bg-purple-500/15 text-purple-400 border-purple-500/30',
  'Feature Request':   'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  'Technical Support': 'bg-red-500/15 text-red-400 border-red-500/30',
}

const PRIORITY_STYLES = {
  High:   'bg-red-500/15 text-red-400 border-red-500/30',
  Medium: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  Low:    'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
}

const PRIORITY_DOTS = {
  High:   'bg-red-400',
  Medium: 'bg-amber-400',
  Low:    'bg-emerald-400',
}

export function CategoryBadge({ category }) {
  const style = CATEGORY_STYLES[category] || 'bg-gray-500/15 text-gray-400 border-gray-500/30'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${style}`}>
      {category}
    </span>
  )
}

export function PriorityBadge({ priority }) {
  const style = PRIORITY_STYLES[priority] || 'bg-gray-500/15 text-gray-400 border-gray-500/30'
  const dot   = PRIORITY_DOTS[priority] || 'bg-gray-400'
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium border ${style}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {priority}
    </span>
  )
}

export function ScoreBadge({ score }) {
  const pct = Math.round(score * 100)
  const style =
    pct >= 70 ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' :
    pct >= 40 ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' :
                'bg-red-500/15 text-red-400 border-red-500/30'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold border ${style}`}>
      {pct}%
    </span>
  )
}

export function DifficultyBadge({ difficulty }) {
  const styles = {
    Easy:   'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    Medium: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    Hard:   'bg-red-500/15 text-red-400 border-red-500/30',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${styles[difficulty] || ''}`}>
      {difficulty}
    </span>
  )
}

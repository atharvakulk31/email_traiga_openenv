export default function ScoreBar({ score, max = 1, showLabel = true, height = 'h-2' }) {
  const pct = Math.min(100, Math.round((score / max) * 100))
  const color =
    pct >= 70 ? 'bg-emerald-500' :
    pct >= 40 ? 'bg-amber-500'  :
                'bg-red-500'

  return (
    <div className="w-full">
      <div className={`w-full bg-gray-800 rounded-full ${height} overflow-hidden`}>
        <div
          className={`${color} ${height} rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-500">{score.toFixed(3)}</span>
          <span className="text-xs text-gray-500">{pct}%</span>
        </div>
      )}
    </div>
  )
}

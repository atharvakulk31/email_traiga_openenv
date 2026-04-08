import { useNavigate } from 'react-router-dom'
import { Mail, Clock, ChevronRight } from 'lucide-react'
import { CategoryBadge, PriorityBadge } from './Badge'

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function excerpt(text, max = 110) {
  if (!text) return ''
  const single = text.replace(/\n+/g, ' ').trim()
  return single.length > max ? single.slice(0, max) + '…' : single
}

export default function EmailCard({ email, isSelected = false }) {
  const navigate = useNavigate()

  return (
    <button
      onClick={() => navigate(`/email/${email.id}`)}
      className={`w-full text-left px-4 py-4 border-b border-gray-800 transition-colors duration-100 group
        ${isSelected ? 'bg-blue-600/10 border-l-2 border-l-blue-500' : 'hover:bg-gray-800/60'}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          {/* Icon */}
          <div className="mt-0.5 w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center flex-shrink-0">
            <Mail size={14} className="text-gray-400" />
          </div>

          {/* Content */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="text-sm font-semibold text-gray-100 truncate">
                {email.subject}
              </span>
            </div>

            <p className="text-xs text-gray-500 mb-2 truncate">
              {email.sender}
            </p>

            <p className="text-xs text-gray-400 leading-relaxed line-clamp-2">
              {excerpt(email.body)}
            </p>

            <div className="flex items-center gap-2 mt-2.5 flex-wrap">
              <CategoryBadge category={email.category} />
              <PriorityBadge priority={email.priority} />
              {email.timestamp && (
                <span className="flex items-center gap-1 text-xs text-gray-600 ml-auto">
                  <Clock size={10} />
                  {formatTime(email.timestamp)}
                </span>
              )}
            </div>
          </div>
        </div>

        <ChevronRight
          size={15}
          className="text-gray-600 group-hover:text-gray-400 transition-colors mt-1 flex-shrink-0"
        />
      </div>
    </button>
  )
}

import { MapPin, RotateCcw, FileText, ChevronLeft, ChevronRight } from 'lucide-react'

export default function HistoryTable({ projects = [], onSelectProject, totalCount = 0 }) {
  return (
    <div className="card history-card">
      <div className="h-row h-head">
        <span>PREVIEW</span>
        <span>PROJECT DETAILS</span>
        <span>LOCATION</span>
        <span className="right">DATE / ITERATION</span>
        <span>STATUS</span>
        <span className="center">ACTION</span>
      </div>

      {projects.length === 0 ? (
        <div style={{ padding: '32px', textAlign: 'center', color: '#8b949b', fontSize: '13px' }}>
          No projects found. Start a new build or adjust your search filter.
        </div>
      ) : (
        projects.map((r) => {
          const status = r.status || (r.archived ? 'ARCHIVED' : 'DEPLOYED')
          const isArchived = status === 'ARCHIVED'
          const statusTone = isArchived ? 'archived' : status === 'ITERATING' ? 'iterating' : status === 'APPROVED' ? 'approved' : 'deployed'
          const dot = status === 'DEPLOYED' ? '●' : status === 'ITERATING' ? '▲' : status === 'APPROVED' ? '◇' : '■'
          const dateStr = r.created_at ? new Date(r.created_at).toISOString().split('T')[0] : r.date || '2023-10-12'

          return (
            <div
              className="h-row"
              key={r.id}
              onClick={() => onSelectProject && onSelectProject(r.id)}
              style={{ cursor: 'pointer' }}
            >
              <span className="h-preview">{r.preview || '🏗️'}</span>
              <span className="h-details">
                <span className={`h-name${isArchived ? ' archived' : ''}`}>{r.name}</span>
                <span className="h-id">ID: #{r.id || 'PRJ-8842'}</span>
              </span>
              <span className="h-location">
                <MapPin size={14} /> {r.location || 'South Asia Regional Site'}
              </span>
              <span className="h-date">
                <span>{dateStr}</span>
                <span className={`h-ver ${r.verTone || ''}`}>{r.version || 'v1.0.0'}</span>
              </span>
              <span className={`h-status ${statusTone}`}>
                <i>{dot}</i> {status}
              </span>
              <span className="h-action">
                {isArchived ? <FileText size={16} /> : <RotateCcw size={16} />}
              </span>
            </div>
          )
        })
      )}

      <div className="h-footer">
        <span>Showing {projects.length} of {totalCount || projects.length} builds</span>
        <span className="h-pager">
          <button><ChevronLeft size={13} /></button>
          <button><ChevronRight size={13} /></button>
        </span>
      </div>
    </div>
  )
}

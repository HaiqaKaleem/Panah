import { AlertTriangle, RefreshCw } from 'lucide-react'

export default function ErrorAlert({ message, onRetry }) {
  if (!message) return null

  return (
    <div style={{
      background: 'rgba(192, 57, 43, 0.15)',
      border: '1px solid rgba(192, 57, 43, 0.4)',
      borderRadius: '6px',
      padding: '12px 16px',
      margin: '12px 0',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      color: '#e74c3c',
      fontSize: '13px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <AlertTriangle size={16} />
        <span>{message}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            background: 'transparent',
            border: '1px solid currentColor',
            color: 'inherit',
            borderRadius: '4px',
            padding: '4px 8px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '11px',
          }}
        >
          <RefreshCw size={12} /> Retry
        </button>
      )}
    </div>
  )
}

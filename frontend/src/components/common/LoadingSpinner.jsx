import { RefreshCw } from 'lucide-react'

export default function LoadingSpinner({ message = 'Loading parametric data...' }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '48px 24px',
      gap: '12px',
      color: '#9aa39a',
    }}>
      <RefreshCw size={28} className="spin-icon" style={{ animation: 'spin 1s linear infinite' }} />
      <span style={{ fontSize: '13px', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
        {message}
      </span>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

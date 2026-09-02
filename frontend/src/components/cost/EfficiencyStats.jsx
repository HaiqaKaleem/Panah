import { SquareKanban } from 'lucide-react'

export default function EfficiencyStats({ costPerM2 = 2.82, structRating = 94, localSourcingRatio = 72 }) {
  return (
    <>
      <div className="cost-head">
        <h3>EFFICIENCY ANALYTICS</h3>
        <SquareKanban size={17} className="muted-icon" />
      </div>
      <div className="eff-stats">
        <div className="eff-stat red">
          <div className="eff-label">COST / M²</div>
          <div className="eff-value">${Number(costPerM2).toFixed(2)}</div>
        </div>
        <div className="eff-stat amber">
          <div className="eff-label">STRUCT. RATING</div>
          <div className="eff-value">{structRating}<small>/100</small></div>
        </div>
        <div className="eff-stat green">
          <div className="eff-label">SOURCING RATIO</div>
          <div className="eff-value">{localSourcingRatio}% <small>Local</small></div>
        </div>
      </div>

      <div className="mini-label">EXPENDITURE DISTRIBUTION</div>
      <div className="dist-bar">
        <div className="seg green" style={{ width: `${localSourcingRatio}%` }} />
        <div className="seg brown" style={{ width: `${Math.max(0, 100 - localSourcingRatio - 15)}%` }} />
        <div className="seg amber" style={{ width: '15%' }} />
      </div>
      <div className="dist-legend">
        <span><i className="sq green" /> Local ({localSourcingRatio}%)</span>
        <span><i className="sq brown" /> Commercial</span>
        <span><i className="sq amber" /> Logistics</span>
      </div>

      <div className="tradeoff">
        <div className="tradeoff-label">COST VS STRUCTURAL INTEGRITY TRADE-OFF (PARETO FRONTIER)</div>
        <svg viewBox="0 0 300 170" className="tradeoff-svg">
          <line x1="168" y1="18" x2="168" y2="150" stroke="#8b949b" strokeDasharray="5 5" />
          <path d="M6 118 C 90 108, 120 42, 170 30 S 262 20, 294 18" fill="none" stroke="#2E7D46" strokeWidth="3" />
          <path d="M6 138 C 90 128, 130 72, 180 58 S 262 46, 294 44" fill="none" stroke="#9C4A2F" strokeWidth="3" />
          <path d="M6 164 C 90 156, 130 112, 180 100 S 240 94, 264 92" fill="none" stroke="#C79A2E" strokeWidth="3" />
          <circle cx="172" cy="29" r="5" fill="#2E7D46" />
          <circle cx="158" cy="64" r="5" fill="#9C4A2F" />
          <circle cx="138" cy="110" r="5" fill="#C79A2E" />
        </svg>
        <span className="config-tag">CURRENT CONFIG</span>
      </div>
    </>
  )
}

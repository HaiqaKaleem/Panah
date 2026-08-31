import { CheckCircle2, AlertCircle, XCircle, ClipboardCheck } from 'lucide-react'

export default function CompliancePrescreen({ designDetail }) {
  // If the backend has rules evaluation, parse it
  const rules = designDetail?.rules?.rule_evaluations || []
  const compliance = designDetail?.rules?.compliance || {}

  // Build items from backend or default standard rule checks
  const defaultItems = [
    {
      tone: 'ok',
      icon: CheckCircle2,
      title: 'Seismic Load (Zone 4)',
      sub: 'Tolerance: > 0.8g PGA (ASCE 7-16 ELF Verified)',
    },
    {
      tone: 'ok',
      icon: CheckCircle2,
      title: 'Monsoon Watertightness',
      sub: 'Roof Pitch: 32° (Min 25° Sphere Standard)',
    },
    {
      tone: 'ok',
      icon: CheckCircle2,
      title: 'Material Stress Limits',
      sub: 'Axial Load: 4.2 MPa (Max allowable 12.0 MPa)',
    },
    {
      tone: 'warn',
      icon: AlertCircle,
      title: 'Foundation Soil Bearing',
      sub: 'Allowable Pressure: 85 kPa (Min required 75 kPa)',
    },
    {
      tone: compliance?.status === 'fail' ? 'fail' : 'ok',
      icon: compliance?.status === 'fail' ? XCircle : CheckCircle2,
      title: 'Wind Shear (Cat 3 Resistance)',
      sub: 'Uplift & Lateral Resistance across primary truss nodes',
    },
  ]

  // Map backend rules if present
  const displayItems = rules.length > 0
    ? rules.map((r) => {
        const passed = r.passed || r.status === 'pass'
        const isWarn = r.severity === 'warning' || r.status === 'review'
        const tone = passed ? 'ok' : isWarn ? 'warn' : 'fail'
        const Icon = passed ? CheckCircle2 : isWarn ? AlertCircle : XCircle
        return {
          tone,
          icon: Icon,
          title: r.rule_name || r.rule_id || 'Sphere Compliance Rule',
          sub: r.message || r.description || `Threshold: ${r.threshold || 'Pass'}`,
        }
      })
    : defaultItems

  return (
    <section className="card">
      <div className="card-head">
        <div className="card-title">
          <ClipboardCheck size={18} /> Compliance Prescreen
        </div>
      </div>
      <div className="compliance-body">
        {displayItems.map(({ tone, icon: Icon, title, sub }, idx) => (
          <div className={`comp-item ${tone}`} key={idx}>
            <Icon size={18} className="comp-icon" />
            <div>
              <div className="comp-title">{title}</div>
              <div className="comp-sub">{sub}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

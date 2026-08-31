import { useState } from 'react'
import { SquareKanban, CheckCircle2, Download } from 'lucide-react'
import { engineeringApi } from '../../api/engineering'

export default function StructuralAnalysis({ designDetail, projectName = 'Panagah Shelter' }) {
  const [generatingReport, setGeneratingReport] = useState(false)
  const [reportSuccess, setReportSuccess] = useState(false)

  const analysis = designDetail?.analysis || {}
  const score = Math.round(
    designDetail?.overall_integrity_score ||
    analysis.overall_integrity_score ||
    analysis.structural_score ||
    78
  )

  const deadLoad = analysis.dead_load_kg || analysis.total_weight_kg || 1240
  const liveLoadCap = analysis.live_load_capacity_kg_m2 || 450
  const maxDeflectionMm = analysis.max_deflection_mm || 14.2

  const handleDownloadReport = async () => {
    setGeneratingReport(true)
    try {
      const blob = await engineeringApi.generateReport({
        project_name: projectName,
        design_data: designDetail?.design || {},
        analysis_data: analysis,
        compliance_data: designDetail?.rules || {},
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${projectName.replace(/\s+/g, '_')}_Engineering_Report.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      setReportSuccess(true)
      setTimeout(() => setReportSuccess(false), 3000)
    } catch (err) {
      console.warn('PDF report download fallback:', err)
      window.print()
    } finally {
      setGeneratingReport(false)
    }
  }

  return (
    <section className="card">
      <div className="card-head">
        <div className="card-title">
          <SquareKanban size={18} /> Structural Analysis
        </div>
      </div>
      <div className="analysis-body">
        <div className="score-row">
          <span>OVERALL INTEGRITY SCORE</span>
          <span className="score-val" style={{ color: score >= 75 ? '#4caf50' : '#e67e22' }}>
            {score}%
          </span>
        </div>
        <div className="score-bar">
          <div
            style={{
              width: `${Math.min(100, score)}%`,
              backgroundColor: score >= 75 ? '#2e7d46' : '#c79a2e',
            }}
          />
        </div>

        <div className="loads">
          <div>
            <div className="load-label">DEAD LOAD</div>
            <div className="load-value">
              {Number(deadLoad).toLocaleString()} <small>kg</small>
            </div>
          </div>
          <div>
            <div className="load-label">LIVE LOAD CAP</div>
            <div className="load-value">
              {Number(liveLoadCap).toLocaleString()} <small>kg/m²</small>
            </div>
          </div>
        </div>

        <div className="mini-label">DEFLECTION CURVE (Z-AXIS)</div>
        <svg className="deflection" viewBox="0 0 220 74">
          <line x1="52" y1="8" x2="168" y2="8" stroke="#9aa39a" strokeDasharray="4 4" />
          <path
            d="M14 62 C 60 62, 78 20, 110 20 C 142 20, 160 62, 206 62"
            fill="none"
            stroke="#1c1c1c"
            strokeWidth="2"
          />
          <circle cx="110" cy="20" r="4" fill="#c0392b" />
          <text x="120" y="14" className="defl-label">
            Max δ: {maxDeflectionMm}mm
          </text>
        </svg>

        <div className="mini-label">STRESS LEGEND (KILO NEWTON/M²)</div>
        <div className="stress-bar" />
        <div className="stress-ticks">
          <span>0.5</span>
          <span>2.0</span>
          <span>5.5+</span>
        </div>

        <button
          className="btn-report"
          onClick={handleDownloadReport}
          disabled={generatingReport}
        >
          {generatingReport ? (
            'COMPILING PDF...'
          ) : reportSuccess ? (
            <>
              <CheckCircle2 size={14} /> REPORT SAVED
            </>
          ) : (
            <>
              <Download size={14} /> EXPORT PDF REPORT
            </>
          )}
        </button>
      </div>
    </section>
  )
}

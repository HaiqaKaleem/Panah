import { useState } from 'react'
import { Layers, Minus, Plus, AlertTriangle, Newspaper, CheckCircle2 } from 'lucide-react'
import { bomApi } from '../../api/bom'

export default function DeploymentScale({
  unitCost = 84.60,
  bambooPerUnit = 24,
  tinPerUnit = 12,
  projectId,
  siteId,
  designId,
}) {
  const [shelters, setShelters] = useState(250)
  const [downloading, setDownloading] = useState(false)
  const [downloaded, setDownloaded] = useState(false)

  const totalBudget = shelters * unitCost
  const totalBamboo = shelters * bambooPerUnit
  const totalTin = shelters * tinPerUnit
  const hasRisk = shelters > 200

  const handleExportBOM = async () => {
    setDownloading(true)
    try {
      if (projectId && siteId && designId) {
        const blob = await bomApi.downloadCsvBlob(projectId, siteId, designId)
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `Panah_BOM_Design_${designId}_Scale_${shelters}.csv`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      } else {
        // Generate CSV client-side fallback
        const csvRows = [
          'Item,Quantity Per Unit,Total Quantity for Deployment,Unit Cost (USD),Total Cost (USD),Availability',
          `Treated Bamboo (3m),${bambooPerUnit},${totalBamboo},0.00,0.00,Site-Sourced`,
          `Corrugated Tin Sheets,${tinPerUnit},${totalTin},4.50,${(totalTin * 4.5).toFixed(2)},Local Bazaar`,
          `Steel Fasteners,32,${shelters * 32},0.80,${(shelters * 32 * 0.8).toFixed(2)},NGO Depot`,
          `Total Deployment Cost,,, ,$${totalBudget.toLocaleString()},`,
        ]
        const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `Panah_BOM_Scale_${shelters}_Units.csv`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      }
      setDownloaded(true)
      setTimeout(() => setDownloaded(false), 3000)
    } catch (err) {
      console.warn('BOM Export error:', err)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <section className="scale-card">
      <div className="cost-head dark">
        <h3>DEPLOYMENT SCALE</h3>
        <Layers size={17} />
      </div>
      <div className="scale-label">FAMILY SHELTERS NEEDED</div>
      <div className="stepper">
        <button onClick={() => setShelters((s) => Math.max(0, s - 10))}>
          <Minus size={15} />
        </button>
        <input
          type="number"
          value={shelters}
          onChange={(e) => setShelters(Math.max(0, parseInt(e.target.value, 10) || 0))}
        />
        <button onClick={() => setShelters((s) => s + 10)}>
          <Plus size={15} />
        </button>
      </div>

      <div className="budget-panel">
        <div className="budget-top">
          <div className="budget-label">
            TOTAL<br />BUDGET<br />REQ.
          </div>
          <div className="budget-value">
            ${Math.round(totalBudget).toLocaleString('en-US')}
          </div>
        </div>
        <div className="budget-bottom">
          <div className="budget-label">
            MATERIAL<br />FOOTPRINT
          </div>
          <div className="footprint">
            <div>
              <strong>{totalBamboo.toLocaleString('en-US')}</strong> Bamboo Culms
            </div>
            <div className="dim">
              {totalTin.toLocaleString('en-US')} Corrugated Sheets
            </div>
          </div>
        </div>
      </div>

      {hasRisk && (
        <div className="risk-alert">
          <div className="risk-title">
            <AlertTriangle size={14} /> PROCUREMENT RISK ALERT
          </div>
          <p>
            Local bazaar tin supply bottleneck detected at &gt;200 units ({totalTin.toLocaleString()} sheets). Consider regional framework agreement.
          </p>
        </div>
      )}

      <button className="btn-export" onClick={handleExportBOM} disabled={downloading}>
        {downloading ? (
          'GENERATING CSV...'
        ) : downloaded ? (
          <>
            <CheckCircle2 size={15} /> BOM DOWNLOADED
          </>
        ) : (
          <>
            <Newspaper size={15} /> EXPORT AUDITABLE BOM
          </>
        )}
      </button>
    </section>
  )
}
